from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import forecast as forecast_router


def make_client():
    app = FastAPI()
    app.include_router(forecast_router.router, prefix="/forecast")
    return TestClient(app)


def test_forecast_serves_from_cache_when_present(monkeypatch):
    cached = [{"date": "2024-01-01", "predicted": 70.0, "lower": 65.0, "upper": 75.0}]
    monkeypatch.setattr(forecast_router, "read_cache", lambda key: cached)
    called = {"run_forecast": False}
    monkeypatch.setattr(forecast_router, "run_forecast", lambda *a, **k: called.__setitem__("run_forecast", True) or [])

    client = make_client()
    resp = client.get("/forecast/", params={"commodity": "crude_oil"})

    assert resp.status_code == 200
    assert resp.json() == cached
    assert called["run_forecast"] is False


def test_forecast_cache_lookup_is_horizon_specific(monkeypatch):
    """
    Regression test: the cache holds only the precomputed 30-day horizon, so a
    request for a different horizon must not be served the 30-day result.
    """
    cached_30 = [{"date": "2024-01-01", "predicted": 70.0, "lower": 65.0, "upper": 75.0}]
    live_90 = [{"date": "2024-03-01", "predicted": 80.0, "lower": 70.0, "upper": 90.0}]

    def fake_read_cache(key):
        return cached_30 if key.endswith(":30") else None

    monkeypatch.setattr(forecast_router, "read_cache", fake_read_cache)
    monkeypatch.setattr(forecast_router, "run_forecast", lambda commodity, horizon: live_90)

    client = make_client()

    assert client.get("/forecast/", params={"commodity": "crude_oil", "horizon": 30}).json() == cached_30
    assert client.get("/forecast/", params={"commodity": "crude_oil", "horizon": 90}).json() == live_90


def test_forecast_falls_back_to_live_computation_when_uncached(monkeypatch):
    live = [{"date": "2024-01-01", "predicted": 71.0, "lower": 66.0, "upper": 76.0}]
    monkeypatch.setattr(forecast_router, "read_cache", lambda key: None)
    monkeypatch.setattr(forecast_router, "run_forecast", lambda commodity, horizon: live)

    client = make_client()
    resp = client.get("/forecast/", params={"commodity": "crude_oil", "horizon": 14})

    assert resp.status_code == 200
    assert resp.json() == live


def test_forecast_maps_value_error_to_400(monkeypatch):
    monkeypatch.setattr(forecast_router, "read_cache", lambda key: None)

    def raise_value_error(commodity, horizon):
        raise ValueError(f"Not enough data for {commodity}")

    monkeypatch.setattr(forecast_router, "run_forecast", raise_value_error)

    client = make_client()
    resp = client.get("/forecast/", params={"commodity": "crude_oil"})

    assert resp.status_code == 400
    assert "crude_oil" in resp.json()["detail"]


def test_forecast_unknown_commodity_returns_404():
    client = make_client()
    resp = client.get("/forecast/", params={"commodity": "unobtainium"})

    assert resp.status_code == 404
    assert "unobtainium" in resp.json()["detail"]


def test_forecast_horizon_out_of_bounds_returns_422():
    client = make_client()
    resp_low = client.get("/forecast/", params={"commodity": "crude_oil", "horizon": 1})
    resp_high = client.get("/forecast/", params={"commodity": "crude_oil", "horizon": 365})

    assert resp_low.status_code == 422
    assert resp_high.status_code == 422
