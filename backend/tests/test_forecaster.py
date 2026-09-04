import datetime

import pytest

from services.db import insert_prices
from ml.forecaster import run_forecast, infer_freq_days
from tests.conftest import make_price_series


def test_infer_freq_days_detects_daily_and_weekly():
    daily = [datetime.date(2024, 1, 1) + datetime.timedelta(days=i) for i in range(10)]
    weekly = [datetime.date(2024, 1, 1) + datetime.timedelta(days=7 * i) for i in range(10)]

    assert infer_freq_days(daily) == 1
    assert infer_freq_days(weekly) == 7


def test_run_forecast_returns_horizon_with_valid_bands(seeded_db):
    result = run_forecast("crude_oil", horizon=14)

    assert len(result) == 14
    for row in result:
        assert set(row.keys()) == {"date", "predicted", "lower", "upper"}
        assert row["lower"] <= row["predicted"] <= row["upper"]

    dates = [r["date"] for r in result]
    assert dates == sorted(dates)
    assert len(set(dates)) == 14  # no duplicate dates


def test_run_forecast_dates_continue_after_history(seeded_db):
    last_history_date = seeded_db[-1]["date"]
    result = run_forecast("crude_oil", horizon=7)
    assert result[0]["date"] > last_history_date


def test_run_forecast_on_weekly_series_steps_weekly(temp_db):
    # EIA spot-price series are weekly; the forecast must step weekly too
    # rather than emitting daily points the model has no basis for.
    insert_prices(make_price_series("weekly_commodity", n=60, step_days=7))

    result = run_forecast("weekly_commodity", horizon=28)

    dates = [datetime.date.fromisoformat(r["date"]) for r in result]
    gaps = {(b - a).days for a, b in zip(dates, dates[1:])}
    assert gaps == {7}
    # 28-day horizon over a weekly cadence -> 4 weekly points
    assert len(result) == 4


def test_weekly_forecast_does_not_oscillate(temp_db):
    """
    Regression test: fitting weekly_seasonality on a weekly series made every
    observation land on the same weekday, leaving the seasonality term
    unidentifiable — Prophet then produced a violent sawtooth across the
    unobserved weekdays. Consecutive predictions should move smoothly.
    """
    records = make_price_series("weekly_commodity", n=80, step_days=7, base=70.0, noise=0.5)
    insert_prices(records)

    result = run_forecast("weekly_commodity", horizon=90)
    predictions = [r["predicted"] for r in result]

    historical = [r["price"] for r in records]
    historical_span = max(historical) - min(historical)

    biggest_step = max(abs(b - a) for a, b in zip(predictions, predictions[1:]))
    assert biggest_step < historical_span, (
        f"forecast jumps {biggest_step:.2f} between consecutive points, "
        f"which exceeds the entire historical range of {historical_span:.2f}"
    )


def test_run_forecast_insufficient_data_raises(temp_db):
    insert_prices(make_price_series("thin_commodity", n=10))

    with pytest.raises(ValueError, match="thin_commodity"):
        run_forecast("thin_commodity")
