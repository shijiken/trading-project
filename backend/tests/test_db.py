from services.db import insert_prices, get_prices, configure_db, get_data_freshness


def test_insert_and_get_prices(temp_db):
    insert_prices([
        {"date": "2024-01-02", "commodity": "crude_oil", "price": 71.0, "unit": "USD/barrel", "source": "EIA"},
        {"date": "2024-01-01", "commodity": "crude_oil", "price": 70.0, "unit": "USD/barrel", "source": "EIA"},
        {"date": "2024-01-01", "commodity": "brent_crude", "price": 75.0, "unit": "USD/barrel", "source": "FRED"},
    ])

    rows = get_prices("crude_oil")
    assert len(rows) == 2
    # ordered ascending by date
    assert [r["date"] for r in rows] == ["2024-01-01", "2024-01-02"]
    assert rows[0]["price"] == 70.0
    assert rows[0]["commodity"] == "crude_oil"
    assert set(rows[0].keys()) == {"date", "commodity", "price", "unit"}


def test_insert_prices_dedup_same_source(temp_db):
    row = {"date": "2024-01-01", "commodity": "crude_oil", "price": 70.0, "unit": "USD/barrel", "source": "EIA"}
    insert_prices([row])
    insert_prices([row])  # duplicate: same date/commodity/source

    rows = get_prices("crude_oil")
    assert len(rows) == 1


def test_insert_prices_distinct_sources_not_deduped(temp_db):
    insert_prices([
        {"date": "2024-01-01", "commodity": "crude_oil", "price": 70.0, "unit": "USD/barrel", "source": "EIA"},
        {"date": "2024-01-01", "commodity": "crude_oil", "price": 71.0, "unit": "USD/barrel", "source": "FRED"},
    ])
    rows = get_prices("crude_oil")
    assert len(rows) == 2


def test_get_prices_filters_by_start_and_end(temp_db):
    insert_prices([
        {"date": d, "commodity": "crude_oil", "price": 70.0, "unit": "USD/barrel", "source": "EIA"}
        for d in ["2024-01-01", "2024-01-05", "2024-01-10", "2024-01-15"]
    ])

    rows = get_prices("crude_oil", start="2024-01-05", end="2024-01-10")
    assert [r["date"] for r in rows] == ["2024-01-05", "2024-01-10"]


def test_get_prices_unknown_commodity_returns_empty(temp_db):
    assert get_prices("does_not_exist") == []


def test_configure_db_enables_wal(temp_db):
    # WAL lets the scheduled ETL write while requests keep reading.
    assert configure_db().lower() == "wal"


def test_get_data_freshness_summarises_each_commodity(temp_db):
    insert_prices([
        {"date": "2024-01-01", "commodity": "crude_oil", "price": 70.0, "unit": "USD/barrel", "source": "EIA"},
        {"date": "2024-01-08", "commodity": "crude_oil", "price": 72.0, "unit": "USD/barrel", "source": "EIA"},
        {"date": "2024-01-01", "commodity": "gasoline", "price": 3.1, "unit": "USD/gallon", "source": "FRED"},
    ])

    summary = {row["commodity"]: row for row in get_data_freshness()}

    assert summary["crude_oil"]["rows"] == 2
    assert summary["crude_oil"]["earliest"] == "2024-01-01"
    assert summary["crude_oil"]["latest"] == "2024-01-08"
    assert summary["gasoline"]["rows"] == 1
