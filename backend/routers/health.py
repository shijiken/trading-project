from datetime import date

from fastapi import APIRouter

from services.db import get_data_freshness
from services.commodities import COMMODITY_UNITS

router = APIRouter()


@router.get("/")
def health():
    """
    Liveness plus data freshness: how current each commodity's history is,
    so the dashboard can show an "as of" indicator and flag stale data.
    """
    freshness = get_data_freshness()
    today = date.today()

    commodities = []
    for row in freshness:
        latest = row["latest"]
        age_days = (today - date.fromisoformat(latest)).days if latest else None
        commodities.append({
            "commodity": row["commodity"],
            "unit":      COMMODITY_UNITS.get(row["commodity"]),
            "rows":      row["rows"],
            "earliest":  row["earliest"],
            "latest":    latest,
            "age_days":  age_days,
        })

    return {
        "status": "ok",
        "checked_at": today.isoformat(),
        "commodities": commodities,
    }
