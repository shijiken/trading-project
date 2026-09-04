from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import anomalies as anomalies_router


def make_client():
    app = FastAPI()
    app.include_router(anomalies_router.router, prefix="/anomalies")
    return TestClient(app)


def test_anomalies_serves_from_cache_when_present(monkeypatch):
    cached = [{"date": "2024-01-01", "commodity": "crude_oil", "price": 500.0, "unit": "USD/barrel", "score": -0.5}]
    monkeypatch.setattr(anomalies_router, "read_cache", lambda key: cached)
    called = {"detect_anomalies": False}
    monkeypatch.setattr(
        anomalies_router, "detect_anomalies",
        lambda *a, **k: called.__setitem__("detect_anomalies", True) or [],
    )

    client = make_client()
    resp = client.get("/anomalies/", params={"commodity": "crude_oil"})

    assert resp.status_code == 200
    assert resp.json() == cached
    assert called["detect_anomalies"] is False


def test_anomalies_date_filtered_request_bypasses_cache(monkeypatch):
    """
    Regression test: the cache holds the full-history result, so a request
    with start/end must recompute rather than return unfiltered anomalies.
    """
    cached = [{"date": "2020-01-01", "commodity": "crude_oil", "price": 20.0, "unit": "USD/barrel", "score": -0.9}]
    filtered = [{"date": "2024-06-01", "commodity": "crude_oil", "price": 95.0, "unit": "USD/barrel", "score": -0.4}]

    monkeypatch.setattr(anomalies_router, "read_cache", lambda key: cached)
    monkeypatch.setattr(anomalies_router, "detect_anomalies", lambda commodity, start=None, end=None: filtered)

    client = make_client()
    resp = client.get("/anomalies/", params={"commodity": "crude_oil", "start": "2024-01-01"})

    assert resp.status_code == 200
    assert resp.json() == filtered


def test_anomalies_falls_back_to_live_computation_when_uncached(monkeypatch):
    live = [{"date": "2024-01-01", "commodity": "crude_oil", "price": 500.0, "unit": "USD/barrel", "score": -0.5}]
    monkeypatch.setattr(anomalies_router, "read_cache", lambda key: None)
    monkeypatch.setattr(anomalies_router, "detect_anomalies", lambda commodity, start=None, end=None: live)

    client = make_client()
    resp = client.get("/anomalies/", params={"commodity": "crude_oil", "start": "2024-01-01", "end": "2024-02-01"})

    assert resp.status_code == 200
    assert resp.json() == live


def test_anomalies_maps_value_error_to_400(monkeypatch):
    monkeypatch.setattr(anomalies_router, "read_cache", lambda key: None)

    def raise_value_error(commodity, start=None, end=None):
        raise ValueError(f"Not enough data to detect anomalies for {commodity}.")

    monkeypatch.setattr(anomalies_router, "detect_anomalies", raise_value_error)

    client = make_client()
    resp = client.get("/anomalies/", params={"commodity": "crude_oil"})

    assert resp.status_code == 400
    assert "crude_oil" in resp.json()["detail"]


def test_anomalies_unknown_commodity_returns_404():
    client = make_client()
    resp = client.get("/anomalies/", params={"commodity": "unobtainium"})

    assert resp.status_code == 404
    assert "unobtainium" in resp.json()["detail"]
