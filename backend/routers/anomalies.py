from fastapi import APIRouter, Query, HTTPException
from ml.cache import read_cache
from ml.anomaly import detect_anomalies

router = APIRouter()

@router.get("/")
def anomalies(
    commodity: str = Query("crude_oil"),
    start:     str = Query(None),
    end:       str = Query(None),
):
    cached = read_cache(f"anomalies:{commodity}")
    if cached:
        return cached

    try:
        return detect_anomalies(commodity, start=start, end=end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))