import datetime

from apscheduler.triggers.interval import IntervalTrigger

import scheduler as scheduler_module


def test_start_scheduler_registers_expected_jobs(monkeypatch):
    # Prevent the real ETL/network/DB work from firing, and prevent the
    # scheduler thread from actually starting — the "startup_etl" job runs
    # immediately once started, which would race with our inspection below.
    monkeypatch.setattr(scheduler_module, "fetch_all_eia", lambda: None)
    monkeypatch.setattr(scheduler_module, "fetch_all_fred", lambda: None)
    monkeypatch.setattr(scheduler_module, "refresh_all_caches", lambda: None)
    monkeypatch.setattr(scheduler_module.BackgroundScheduler, "start", lambda self: None)

    bg_scheduler = scheduler_module.start_scheduler()

    jobs = {job.id: job for job in bg_scheduler.get_jobs()}
    assert "startup_etl" in jobs

    interval_jobs = [j for j in bg_scheduler.get_jobs() if j.id != "startup_etl"]
    assert len(interval_jobs) == 1
    trigger = interval_jobs[0].trigger
    assert isinstance(trigger, IntervalTrigger)
    assert trigger.interval == datetime.timedelta(hours=6)
