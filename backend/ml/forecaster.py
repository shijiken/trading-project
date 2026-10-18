import math
import statistics

import pandas as pd
from prophet import Prophet
from services.db import get_prices


def infer_freq_days(dates) -> int:
    """
    Median gap, in days, between consecutive observations.

    EIA's spot-price series are weekly (7-day gaps) while FRED's Brent series
    is daily, so the cadence has to be inferred rather than assumed.
    """
    gaps = [(b - a).days for a, b in zip(dates, dates[1:]) if (b - a).days > 0]
    if not gaps:
        return 1
    return max(1, int(statistics.median(gaps)))


def run_forecast(commodity: str, horizon: int = 30) -> list[dict]:
    """
    Pulls historical prices from DB, fits Prophet, and returns predictions
    covering the next `horizon` DAYS.

    The number of returned rows depends on the series' own cadence: a weekly
    series over a 30-day horizon yields ~5 weekly points, not 30 daily ones.
    """
    records = get_prices(commodity)

    if len(records) < 30:
        raise ValueError(f"Not enough data for {commodity} — need at least 30 rows.")

    # Prophet expects columns named exactly 'ds' and 'y'
    df = pd.DataFrame(records)[["date", "price"]]
    df.columns = ["ds", "y"]
    df["ds"] = pd.to_datetime(df["ds"])

    freq_days = infer_freq_days(list(df["ds"].dt.date))

    # A weekly (or coarser) series has every observation on the same weekday,
    # so a weekly seasonality term is unidentifiable — fitting one produces
    # wild swings on the weekdays that were never observed.
    weekly_seasonality = freq_days < 7

    model = Prophet(
        interval_width=0.95,        # 95% confidence band
        daily_seasonality=False,
        weekly_seasonality=weekly_seasonality,
        yearly_seasonality=True,
    )
    model.fit(df)

    # Step the future at the series' own cadence so predictions land on dates
    # of the same kind as the history.
    periods = max(1, math.ceil(horizon / freq_days))
    future = model.make_future_dataframe(periods=periods, freq=f"{freq_days}D")
    forecast = model.predict(future)

    # Return only the future horizon, not historical fitted values
    result = forecast.tail(periods)[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    return [
        {
            "date":      row["ds"].strftime("%Y-%m-%d"),
            "predicted": round(row["yhat"], 2),
            "lower":     round(row["yhat_lower"], 2),
            "upper":     round(row["yhat_upper"], 2),
        }
        for _, row in result.iterrows()
    ]
