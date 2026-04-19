from fastapi import APIRouter, Query, HTTPException
from ml.cache import read_cache
from ml.forecaster import run_forecast

router = APIRouter()

@router.get("/")
def forecast(
    commodity: str = Query("crude_oil"),
    horizon:   int = Query(30, ge=7, le=90),
):
    # Serve from cache if available
    cached = read_cache(f"forecast:{commodity}")
    if cached:
        return cached

    # Fall back to live computation
    try:
        return run_forecast(commodity, horizon)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))