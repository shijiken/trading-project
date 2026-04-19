import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()
EIA_KEY = os.getenv("EIA_API_KEY")
BASE_URL = "https://api.eia.gov/v2"
PAGE_SIZE = 5000
REQUEST_TIMEOUT = 30

log = logging.getLogger(__name__)

EIA_SERIES = {
    "crude_oil":    ("petroleum/pri/spt/data/", "RWTC",                    "USD/barrel"),
    "natural_gas":  ("natural-gas/pri/sum/data/", "RNGWHHD",               "USD/MMBtu"),
    "heating_oil":  ("petroleum/pri/spt/data/", "EER_EPD2F_PF4_RGC_DPG",   "USD/gallon"),
}

def fetch_eia_series(commodity: str, start: str = "2020-01-01") -> list[dict]:
    path, series_id, unit = EIA_SERIES[commodity]
    url = f"{BASE_URL}/{path}"

    records: list[dict] = []
    offset = 0
    while True:
        params = {
            "api_key": EIA_KEY,
            "data[]": "value",
            "facets[series][]": series_id,
            "start": start,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "length": PAGE_SIZE,
            "offset": offset,
        }
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get("response", {}).get("data", [])

        for row in data:
            if row.get("value") is None:
                continue
            records.append({
                "date":      row["period"],
                "commodity": commodity,
                "price":     float(row["value"]),
                "unit":      unit,
                "source":    "EIA",
            })

        if len(data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    print(f"  Fetched {len(records)} rows for {commodity} from EIA.")
    return records

def fetch_all_eia():
    from services.db import insert_prices
    for commodity in EIA_SERIES:
        try:
            records = fetch_eia_series(commodity)
            insert_prices(records)
        except Exception:
            log.exception("EIA fetch failed for %s", commodity)