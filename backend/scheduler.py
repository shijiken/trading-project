import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from services.eia import fetch_all_eia
from services.fred import fetch_all_fred
from ml.cache import refresh_all_caches, init_cache_table

log = logging.getLogger(__name__)

def run_etl():
    log.info("Running scheduled ETL")
    try:
        fetch_all_eia()
    except Exception:
        log.exception("EIA ETL step failed")
    try:
        fetch_all_fred()
    except Exception:
        log.exception("FRED ETL step failed")
    try:
        refresh_all_caches()        # recompute ML after new data lands
    except Exception:
        log.exception("ML cache refresh failed")
    
def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_etl,
        "interval",
        hours=6,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        run_etl,
        "date",                     # runs once, immediately on start
        id="startup_etl",
    )
    scheduler.start()
    return scheduler

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    log.info("Scheduler started. Press Ctrl+C to stop.")
    scheduler = start_scheduler()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()