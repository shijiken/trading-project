import pandas as pd
from prophet import Prophet
from services.db import get_prices

def run_forecast(commodity: str, horizon: int = 30) -> list[dict]:
    """
    Pulls historical prices from DB, fits Prophet,
    returns horizon days of future predictions.
    """
    records = get_prices(commodity)

    if len(records) < 30:
        raise ValueError(f"Not enough data for {commodity} — need at least 30 rows.")

    # Prophet expects columns named exactly 'ds' and 'y'
    df = pd.DataFrame(records)[["date", "price"]]
    df.columns = ["ds", "y"]
    df["ds"] = pd.to_datetime(df["ds"])

    model = Prophet(
        interval_width=0.95,        # 95% confidence band
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=horizon)
    forecast = model.predict(future)

    # Return only the future horizon, not historical fitted values
    result = forecast.tail(horizon)[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    return [
        {
            "date":      row["ds"].strftime("%Y-%m-%d"),
            "predicted": round(row["yhat"], 2),
            "lower":     round(row["yhat_lower"], 2),
            "upper":     round(row["yhat_upper"], 2),
        }
        for _, row in result.iterrows()
    ]