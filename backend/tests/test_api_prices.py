from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import prices as prices_router
from services.db import insert_prices


def make_client():
    app = FastAPI()
    app.include_router(prices_router.router, prefix="/prices")
    return TestClient(app)


def test_get_prices_returns_seeded_rows(temp_db):
    insert_prices([
        {"date": "2024-01-01", "commodity": "crude_oil", "price": 70.0, "unit": "USD/barrel", "source": "EIA"},
        {"date": "2024-01-02", "commodity": "crude_oil", "price": 71.0, "unit": "USD/barrel", "source": "EIA"},
    ])
    client = make_client()

    resp = client.get("/prices/", params={"commodity": "crude_oil"})

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["date"] == "2024-01-01"
    assert body[0]["price"] == 70.0


def test_get_prices_filters_by_date_range(temp_db):
    insert_prices([
        {"date": d, "commodity": "crude_oil", "price": 70.0, "unit": "USD/barrel", "source": "EIA"}
        for d in ["2024-01-01", "2024-01-05", "2024-01-10"]
    ])
    client = make_client()

    resp = client.get("/prices/", params={"commodity": "crude_oil", "start": "2024-01-02", "end": "2024-01-10"})

    assert [r["date"] for r in resp.json()] == ["2024-01-05", "2024-01-10"]


def test_get_prices_unknown_commodity_returns_404(temp_db):
    client = make_client()
    resp = client.get("/prices/", params={"commodity": "unobtainium"})
    assert resp.status_code == 404
    assert "unobtainium" in resp.json()["detail"]


def test_get_prices_known_commodity_with_no_rows_returns_empty_list(temp_db):
    client = make_client()
    resp = client.get("/prices/", params={"commodity": "heating_oil"})
    assert resp.status_code == 200
    assert resp.json() == []
