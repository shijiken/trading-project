import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
REQUEST_TIMEOUT = 30

log = logging.getLogger(__name__)

# FRED series IDs
FRED_SERIES = {
    "brent_crude":  ("DCOILBRENTEU", "USD/barrel"),
    "gasoline":     ("GASREGCOVW",   "USD/gallon"),
    "us_cpi":       ("CPIAUCSL",     "index"),      # useful macro context
}

def fetch_fred_series(commodity: str, start: str = "2020-01-01") -> list[dict]:
    series_id, unit = FRED_SERIES[commodity]

    params = {
        "series_id":        series_id,
        "api_key":          FRED_KEY,
        "file_type":        "json",
        "observation_start": start,
        "sort_order":       "asc",
    }

    resp = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    observations = resp.json().get("observations", [])

    records = []
    for obs in observations:
        if obs["value"] == ".":   # FRED uses "." for missing values
            continue
        records.append({
            "date":      obs["date"],
            "commodity": commodity,
            "price":     float(obs["value"]),
            "unit":      unit,
            "source":    "FRED",
        })

    print(f"  Fetched {len(records)} rows for {commodity} from FRED.")
    return records

def fetch_all_fred():
    from services.db import insert_prices
    for commodity in FRED_SERIES:
        try:
            records = fetch_fred_series(commodity)
            insert_prices(records)
        except Exception:
            log.exception("FRED fetch failed for %s", commodity)