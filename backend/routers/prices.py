from fastapi import APIRouter, Query, HTTPException
from services.db import get_prices
from services.commodities import is_known, KNOWN_COMMODITIES

router = APIRouter()

@router.get("/")
def prices(
    commodity: str = Query("crude_oil"),
    start:     str = Query(None),
    end:       str = Query(None),
):
    if not is_known(commodity):
        raise HTTPException(
            status_code=404,
            detail=f"Unknown commodity '{commodity}'. Known: {sorted(KNOWN_COMMODITIES)}",
        )
    return get_prices(commodity, start=start, end=end)
