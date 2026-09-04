import pytest

from services.db import insert_prices
from ml.anomaly import detect_anomalies
from tests.conftest import make_price_series


def test_detect_anomalies_flags_injected_spike(temp_db):
    records = make_price_series("crude_oil", n=60, base=70.0, noise=0.5)
    spike_date = records[30]["date"]
    records[30] = {**records[30], "price": 500.0}  # obvious outlier
    insert_prices(records)

    anomalies = detect_anomalies("crude_oil")

    flagged_dates = {a["date"] for a in anomalies}
    assert spike_date in flagged_dates
    for a in anomalies:
        assert set(a.keys()) == {"date", "commodity", "price", "unit", "score"}
    # worst (most negative score) anomalies first
    scores = [a["score"] for a in anomalies]
    assert scores == sorted(scores)
    # the injected spike should be the single worst anomaly
    assert anomalies[0]["date"] == spike_date


def test_detect_anomalies_respects_date_range(temp_db):
    records = make_price_series("crude_oil", n=60)
    insert_prices(records)

    start = records[40]["date"]
    anomalies = detect_anomalies("crude_oil", start=start)

    assert all(a["date"] >= start for a in anomalies)


def test_detect_anomalies_insufficient_data_raises(temp_db):
    insert_prices(make_price_series("thin_commodity", n=5))

    with pytest.raises(ValueError, match="thin_commodity"):
        detect_anomalies("thin_commodity")
