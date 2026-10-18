import sqlite3
import json
from ml.forecaster import run_forecast
from ml.anomaly import detect_anomalies
from services.db import DB_PATH as PRICES_DB_PATH

# Same file as the prices table — the freshness check in read_cache joins
# against it. (A relative path here used to depend on the working directory.)
DB_PATH = PRICES_DB_PATH

COMMODITIES = ["crude_oil", "natural_gas", "brent_crude", "gasoline", "heating_oil"]

# Horizon (in days) precomputed on the schedule. Other horizons fall through
# to live computation, so the cache key has to carry the horizon — otherwise a
# request for 90 days would be served the cached 30-day forecast.
CACHED_HORIZON = 30


def forecast_key(commodity: str, horizon: int = CACHED_HORIZON) -> str:
    return f"forecast:{commodity}:{horizon}"


def anomalies_key(commodity: str) -> str:
    return f"anomalies:{commodity}"

def init_cache_table():
    conn = sqlite3.connect(DB_PATH)
    columns = {r[1] for r in conn.execute("PRAGMA table_info(ml_cache)")}
    if columns and "data_as_of" not in columns:
        # Pre-freshness schema. The cache is disposable, so rebuild it rather
        # than migrate — the warm-up refresh repopulates it.
        conn.execute("DROP TABLE ml_cache")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ml_cache (
            key        TEXT PRIMARY KEY,
            result     TEXT NOT NULL,
            commodity  TEXT,
            data_as_of TEXT,
            updated    TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

def latest_price_date(commodity: str) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT MAX(date) FROM prices WHERE commodity = ?", (commodity,)
    ).fetchone()
    conn.close()
    return row[0]

def write_cache(key: str, data: list[dict], commodity: str | None = None, data_as_of: str | None = None):
    """
    `data_as_of` is the latest price date the result was computed from. Capture
    it BEFORE fitting: if new rows land mid-fit, the entry then looks stale
    (safe: it gets recomputed) rather than looking fresh when it isn't.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO ml_cache (key, result, commodity, data_as_of, updated)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (key, json.dumps(data), commodity, data_as_of))
    conn.commit()
    conn.close()

def read_cache(key: str) -> list[dict] | None:
    """
    Returns the cached result, or None on a miss. An entry counts as a miss if
    prices newer than the ones it was computed from have since been loaded —
    e.g. the post-ETL refresh failed for that commodity — so callers fall back
    to live computation instead of serving a stale forecast.
    """
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("""
        SELECT c.result, c.commodity, c.data_as_of,
               (SELECT MAX(date) FROM prices p WHERE p.commodity = c.commodity)
        FROM ml_cache c
        WHERE c.key = ?
    """, (key,)).fetchone()
    conn.close()
    if not row:
        return None
    result, commodity, data_as_of, current_latest = row
    if commodity is not None and data_as_of != current_latest:
        return None
    return json.loads(result)

def refresh_all_caches():
    """Call this on startup and every 6 hours via scheduler."""
    print("Refreshing ML caches...")
    for commodity in COMMODITIES:
        as_of = latest_price_date(commodity)
        try:
            forecast = run_forecast(commodity, horizon=CACHED_HORIZON)
            write_cache(forecast_key(commodity), forecast, commodity, as_of)
            print(f"  Cached forecast for {commodity}")
        except Exception as e:
            print(f"  Forecast failed for {commodity}: {e}")

        try:
            anomalies = detect_anomalies(commodity)
            write_cache(anomalies_key(commodity), anomalies, commodity, as_of)
            print(f"  Cached anomalies for {commodity}")
        except Exception as e:
            print(f"  Anomaly detection failed for {commodity}: {e}")