from apscheduler.schedulers.background import BackgroundScheduler
from services.eia import fetch_all_eia
from services.fred import fetch_all_fred
import time

def run_etl():
    print("Running scheduled ETL...")
    fetch_all_eia()
    fetch_all_fred()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_etl, "interval", hours=6)
    scheduler.start()
    return scheduler

if __name__ == "__main__":
    print("Scheduler started. Press Ctrl+C to stop.")
    scheduler = start_scheduler()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()