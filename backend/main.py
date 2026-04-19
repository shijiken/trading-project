from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import forecast, anomalies
from ml.cache import init_cache_table, refresh_all_caches
from scheduler import start_scheduler

app = FastAPI(title="Commodity Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecast.router,   prefix="/forecast")
app.include_router(anomalies.router,  prefix="/anomalies")

@app.on_event("startup")
def on_startup():
    init_cache_table()
    refresh_all_caches()   # precompute on boot
    start_scheduler()