import logging
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from routers import forecast, anomalies, prices, health
from ml.cache import init_cache_table, refresh_all_caches
from services.db import configure_db
from scheduler import start_scheduler

log = logging.getLogger(__name__)

app = FastAPI(title="Commodity Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Price history responses are long JSON arrays that compress extremely well.
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(forecast.router,   prefix="/forecast")
app.include_router(anomalies.router,  prefix="/anomalies")
app.include_router(prices.router,     prefix="/prices")
app.include_router(health.router,     prefix="/health")

@app.on_event("startup")
def on_startup():
    configure_db()
    init_cache_table()

    # Warm the ML caches off the critical path — fitting Prophet for every
    # commodity takes seconds, and the endpoints already fall back to live
    # computation on a cache miss, so the API can serve immediately.
    threading.Thread(target=_warm_caches, name="cache-warmup", daemon=True).start()

    start_scheduler()

def _warm_caches():
    try:
        refresh_all_caches()
    except Exception:
        log.exception("Initial ML cache warm-up failed")
