import sqlite3
import json
from ml.forecaster import run_forecast
from ml.anomaly import detect_anomalies

DB_PATH = "commodity.db"

COMMODITIES = ["crude_oil", "natural_gas", "brent_crude", "gasoline"]

def init_cache_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ml_cache (
            key       TEXT PRIMARY KEY,
            result    TEXT NOT NULL,
            updated   TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

def write_cache(key: str, data: list[dict]):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO ml_cache (key, result, updated)
        VALUES (?, ?, datetime('now'))
    """, (key, json.dumps(data)))
    conn.commit()
    conn.close()

def read_cache(key: str) -> list[dict] | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT result FROM ml_cache WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

def refresh_all_caches():
    """Call this on startup and every 6 hours via scheduler."""
    print("Refreshing ML caches...")
    for commodity in COMMODITIES:
        try:
            forecast = run_forecast(commodity, horizon=30)
            write_cache(f"forecast:{commodity}", forecast)
            print(f"  Cached forecast for {commodity}")
        except Exception as e:
            print(f"  Forecast failed for {commodity}: {e}")

        try:
            anomalies = detect_anomalies(commodity)
            write_cache(f"anomalies:{commodity}", anomalies)
            print(f"  Cached anomalies for {commodity}")
        except Exception as e:
            print(f"  Anomaly detection failed for {commodity}: {e}")