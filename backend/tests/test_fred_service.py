from unittest.mock import MagicMock

import services.fred as fred


def _resp(observations):
    m = MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = {"observations": observations}
    return m


def test_fred_series_config_unchanged():
    assert fred.FRED_SERIES["brent_crude"] == ("DCOILBRENTEU", "USD/barrel")
    assert fred.FRED_SERIES["gasoline"] == ("GASREGCOVW", "USD/gallon")


def test_fetch_fred_series_maps_fields_and_skips_missing(monkeypatch):
    monkeypatch.setattr(
        fred, "get_with_retry",
        MagicMock(return_value=_resp([
            {"date": "2024-01-01", "value": "75.2"},
            {"date": "2024-01-02", "value": "."},  # FRED's missing-value marker
        ])),
    )

    records = fred.fetch_fred_series("brent_crude")

    assert records == [
        {"date": "2024-01-01", "commodity": "brent_crude", "price": 75.2, "unit": "USD/barrel", "source": "FRED"},
    ]


def test_fetch_all_fred_continues_after_one_commodity_fails(monkeypatch):
    calls = []

    def fake_fetch(commodity, start="2020-01-01"):
        calls.append(commodity)
        if commodity == "us_cpi":
            raise RuntimeError("boom")
        return [{"date": "2024-01-01", "commodity": commodity, "price": 1.0, "unit": "u", "source": "FRED"}]

    inserted = []
    monkeypatch.setattr(fred, "fetch_fred_series", fake_fetch)
    monkeypatch.setattr("services.db.insert_prices", lambda records: inserted.append(records))

    fred.fetch_all_fred()

    assert set(calls) == set(fred.FRED_SERIES.keys())
    assert len(inserted) == len(fred.FRED_SERIES) - 1
