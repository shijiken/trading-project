from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import health as health_router
from services.db import insert_prices


def make_client():
    app = FastAPI()
    app.include_router(health_router.router, prefix="/health")
    return TestClient(app)


def test_health_reports_ok_with_empty_db(temp_db):
    resp = make_client().get("/health/")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["commodities"] == []


def test_health_reports_row_counts_and_freshness(temp_db):
    recent = (date.today() - timedelta(days=3)).isoformat()
    insert_prices([
        {"date": "2024-01-01", "commodity": "crude_oil", "price": 70.0, "unit": "USD/barrel", "source": "EIA"},
        {"date": recent, "commodity": "crude_oil", "price": 80.0, "unit": "USD/barrel", "source": "EIA"},
    ])

    body = make_client().get("/health/").json()
    entry = next(c for c in body["commodities"] if c["commodity"] == "crude_oil")

    assert entry["rows"] == 2
    assert entry["earliest"] == "2024-01-01"
    assert entry["latest"] == recent
    assert entry["age_days"] == 3
    assert entry["unit"] == "USD/barrel"
