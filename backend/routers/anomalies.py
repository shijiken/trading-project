from fastapi import APIRouter, Query, HTTPException
from ml.cache import read_cache, anomalies_key
from ml.anomaly import detect_anomalies
from services.commodities import is_known, KNOWN_COMMODITIES

router = APIRouter()

@router.get("/")
def anomalies(
    commodity: str = Query("crude_oil"),
    start:     str = Query(None),
    end:       str = Query(None),
):
    if not is_known(commodity):
        raise HTTPException(
            status_code=404,
            detail=f"Unknown commodity '{commodity}'. Known: {sorted(KNOWN_COMMODITIES)}",
        )

    # The cache holds the full-history result, so only serve it for unfiltered requests
    if not start and not end:
        cached = read_cache(anomalies_key(commodity))
        if cached:
            return cached

    try:
        return detect_anomalies(commodity, start=start, end=end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
