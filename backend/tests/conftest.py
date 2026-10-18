import math
import random

import pytest

from db.setup import init_db
import services.db as db_module
import ml.cache as cache_module
from services.db import insert_prices


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Isolated sqlite db for a single test — never touches the real commodity.db."""
    db_path = str(tmp_path / "test_commodity.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(cache_module, "DB_PATH", db_path)

    init_db(db_path)
    cache_module.init_cache_table()
    return db_path


def make_price_series(
    commodity, n=90, start="2024-01-01", base=70.0, noise=0.5, source="TEST", step_days=1
):
    """
    Deterministic synthetic price series for ML tests.

    `step_days=7` produces a weekly series like the EIA spot-price feeds.
    """
    import datetime

    rng = random.Random(42)
    d0 = datetime.date.fromisoformat(start)
    records = []
    for i in range(n):
        date = (d0 + datetime.timedelta(days=i * step_days)).isoformat()
        price = base + 5 * math.sin(i / 7) + rng.uniform(-noise, noise)
        records.append({
            "date": date,
            "commodity": commodity,
            "price": round(price, 2),
            "unit": "USD/barrel",
            "source": source,
        })
    return records


@pytest.fixture
def seeded_db(temp_db):
    """temp_db pre-loaded with a clean synthetic price series for 'crude_oil'."""
    records = make_price_series("crude_oil", n=90)
    insert_prices(records)
    return records
