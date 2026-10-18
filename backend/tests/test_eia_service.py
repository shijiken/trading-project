from unittest.mock import MagicMock

import services.eia as eia


def _resp(data):
    m = MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = {"response": {"data": data}}
    return m


def test_natural_gas_series_uses_fixed_route_and_id():
    # Regression check: the app previously pointed at natural-gas/pri/sum/data/ with
    # series RNGWHHD, which returns zero rows. The correct route is pri/fut.
    path, series_id, unit = eia.EIA_SERIES["natural_gas"]
    assert path == "natural-gas/pri/fut/data/"
    assert series_id == "RNGWHHD"
    assert unit == "USD/MMBtu"


def test_heating_oil_series_uses_fixed_id():
    # Regression check: EER_EPD2F_PF4_RGC_DPG returns zero rows; the NY Harbor
    # No. 2 Heating Oil Spot Price series id is EER_EPD2F_PF4_Y35NY_DPG.
    path, series_id, unit = eia.EIA_SERIES["heating_oil"]
    assert path == "petroleum/pri/spt/data/"
    assert series_id == "EER_EPD2F_PF4_Y35NY_DPG"
    assert unit == "USD/gallon"


def test_fetch_eia_series_maps_fields_and_skips_nulls(monkeypatch):
    monkeypatch.setattr(eia, "PAGE_SIZE", 5000)
    monkeypatch.setattr(
        eia, "get_with_retry",
        MagicMock(return_value=_resp([
            {"period": "2024-01-01", "value": "70.5"},
            {"period": "2024-01-02", "value": None},  # skipped
        ])),
    )

    records = eia.fetch_eia_series("crude_oil", start="2024-01-01")

    assert records == [
        {"date": "2024-01-01", "commodity": "crude_oil", "price": 70.5, "unit": "USD/barrel", "source": "EIA"},
    ]


def test_fetch_eia_series_paginates_until_short_page(monkeypatch):
    monkeypatch.setattr(eia, "PAGE_SIZE", 2)
    page1 = [{"period": "2024-01-01", "value": "1"}, {"period": "2024-01-02", "value": "2"}]
    page2 = [{"period": "2024-01-03", "value": "3"}]  # shorter than PAGE_SIZE -> stop
    mock_get = MagicMock(side_effect=[_resp(page1), _resp(page2)])
    monkeypatch.setattr(eia, "get_with_retry", mock_get)

    records = eia.fetch_eia_series("crude_oil")

    assert [r["date"] for r in records] == ["2024-01-01", "2024-01-02", "2024-01-03"]
    assert mock_get.call_count == 2
    # second call paginated with the right offset
    assert mock_get.call_args_list[1].kwargs["params"]["offset"] == 2


def test_fetch_all_eia_continues_after_one_commodity_fails(monkeypatch):
    calls = []

    def fake_fetch(commodity, start="2020-01-01"):
        calls.append(commodity)
        if commodity == "natural_gas":
            raise RuntimeError("boom")
        return [{"date": "2024-01-01", "commodity": commodity, "price": 1.0, "unit": "u", "source": "EIA"}]

    inserted = []
    monkeypatch.setattr(eia, "fetch_eia_series", fake_fetch)
    monkeypatch.setattr("services.db.insert_prices", lambda records: inserted.append(records))

    eia.fetch_all_eia()

    assert set(calls) == set(eia.EIA_SERIES.keys())
    # the two commodities that didn't raise still got inserted
    assert len(inserted) == len(eia.EIA_SERIES) - 1
