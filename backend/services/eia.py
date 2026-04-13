import requests
import os
from dotenv import load_dotenv

load_dotenv()
EIA_KEY = os.getenv("EIA_API_KEY")
BASE_URL = "https://api.eia.gov/v2"

# Commodity series IDs you care about
EIA_SERIES = {
    "crude_oil":    ("petroleum/pri/spt/data/", "RWTC"),   # WTI spot price
    "natural_gas":  ("natural-gas/pri/sum/data/", "RNGWHHD"),
    "heating_oil":  ("petroleum/pri/spt/data/", "EER_EPD2F_PF4_RGC_DPG"),
}

def fetch_eia_series(commodity: str, start: str = "2020-01-01") -> list[dict]:
    path, series_id = EIA_SERIES[commodity]
    url = f"{BASE_URL}/{path}"

    params = {
        "api_key": EIA_KEY,
        "data[]": "value",
        "facets[series][]": series_id,
        "start": start,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": 5000,
    }

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json().get("response", {}).get("data", [])

    records = []
    for row in data:
        if row.get("value") is None:
            continue
        records.append({
            "date":      row["period"],
            "commodity": commodity,
            "price":     float(row["value"]),
            "unit":      "USD/barrel" if commodity == "crude_oil" else "USD/MMBtu",
            "source":    "EIA",
        })

    print(f"  Fetched {len(records)} rows for {commodity} from EIA.")
    return records

def fetch_all_eia():
    from services.db import insert_prices
    for commodity in EIA_SERIES:
        records = fetch_eia_series(commodity)
        insert_prices(records)