from fastapi import APIRouter, Query, HTTPException
from ml.cache import read_cache, forecast_key
from ml.forecaster import run_forecast
from services.commodities import is_known, KNOWN_COMMODITIES

router = APIRouter()

@router.get("/")
def forecast(
    commodity: str = Query("crude_oil"),
    horizon:   int = Query(30, ge=7, le=90),
):
    if not is_known(commodity):
        raise HTTPException(
            status_code=404,
            detail=f"Unknown commodity '{commodity}'. Known: {sorted(KNOWN_COMMODITIES)}",
        )

    # Serve from cache if this exact horizon was precomputed
    cached = read_cache(forecast_key(commodity, horizon))
    if cached:
        return cached

    # Fall back to live computation
    try:
        return run_forecast(commodity, horizon)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
