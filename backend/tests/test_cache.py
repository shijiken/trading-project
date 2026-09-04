import ml.cache as cache


def test_write_and_read_cache_roundtrip(temp_db):
    data = [{"date": "2024-01-01", "predicted": 70.0, "lower": 65.0, "upper": 75.0}]
    cache.write_cache("forecast:crude_oil", data)

    assert cache.read_cache("forecast:crude_oil") == data


def test_read_cache_missing_key_returns_none(temp_db):
    assert cache.read_cache("does:not:exist") is None


def test_write_cache_overwrites_existing_key(temp_db):
    cache.write_cache("forecast:crude_oil", [{"a": 1}])
    cache.write_cache("forecast:crude_oil", [{"a": 2}])

    assert cache.read_cache("forecast:crude_oil") == [{"a": 2}]


def test_refresh_all_caches_writes_all_commodities_and_survives_failures(temp_db, monkeypatch):
    def fake_forecast(commodity, horizon=30):
        if commodity == "gasoline":
            raise RuntimeError("forecast boom")
        return [{"date": "2024-01-01", "predicted": 1.0, "lower": 0.5, "upper": 1.5}]

    def fake_anomalies(commodity, start=None, end=None):
        if commodity == "heating_oil":
            raise RuntimeError("anomaly boom")
        return [{"date": "2024-01-01", "commodity": commodity, "price": 1.0, "unit": "u", "score": -0.1}]

    monkeypatch.setattr(cache, "run_forecast", fake_forecast)
    monkeypatch.setattr(cache, "detect_anomalies", fake_anomalies)

    cache.refresh_all_caches()

    for commodity in cache.COMMODITIES:
        forecast_result = cache.read_cache(cache.forecast_key(commodity))
        anomaly_result = cache.read_cache(cache.anomalies_key(commodity))
        if commodity == "gasoline":
            assert forecast_result is None
        else:
            assert forecast_result is not None
        if commodity == "heating_oil":
            assert anomaly_result is None
        else:
            assert anomaly_result is not None


def test_heating_oil_is_cached():
    # Regression check: heating_oil was previously missing from COMMODITIES,
    # so it never got a precomputed forecast/anomaly cache entry.
    assert "heating_oil" in cache.COMMODITIES


def test_forecast_key_encodes_horizon():
    # Regression check: without the horizon in the key, a 90-day request was
    # served the cached 30-day forecast.
    assert cache.forecast_key("crude_oil", 30) != cache.forecast_key("crude_oil", 90)
    assert cache.forecast_key("crude_oil") == cache.forecast_key("crude_oil", cache.CACHED_HORIZON)


def test_refresh_writes_under_the_cached_horizon_key(temp_db, monkeypatch):
    monkeypatch.setattr(cache, "run_forecast", lambda commodity, horizon: [{"h": horizon}])
    monkeypatch.setattr(cache, "detect_anomalies", lambda commodity, start=None, end=None: [])

    cache.refresh_all_caches()

    assert cache.read_cache(cache.forecast_key("crude_oil", cache.CACHED_HORIZON)) == [{"h": cache.CACHED_HORIZON}]
    assert cache.read_cache(cache.forecast_key("crude_oil", 90)) is None
