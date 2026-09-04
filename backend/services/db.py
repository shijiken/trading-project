import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent.parent / "commodity.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn

def configure_db():
    """
    Switch the database to WAL so the 6-hourly ETL write doesn't block reads.
    journal_mode is persisted in the file itself, so this only has to stick once.
    """
    conn = get_conn()
    mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.commit()
    conn.close()
    return mode

def insert_prices(records: list[dict]):
    """
    records: list of {date, commodity, price, unit, source}
    Skips duplicates silently via INSERT OR IGNORE.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany("""
        INSERT OR IGNORE INTO prices (date, commodity, price, unit, source)
        VALUES (:date, :commodity, :price, :unit, :source)
    """, records)
    conn.commit()
    inserted = cur.rowcount
    conn.close()
    print(f"  Inserted {inserted} new rows.")

def get_prices(commodity: str, start: str | None = None, end: str | None = None):
    conn = get_conn()
    query = "SELECT date, commodity, price, unit FROM prices WHERE commodity = ?"
    params = [commodity]

    if start:
        query += " AND date >= ?"
        params.append(start)
    if end:
        query += " AND date <= ?"
        params.append(end)

    query += " ORDER BY date ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_data_freshness():
    """Per-commodity row count and latest observation date, for /health."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT commodity,
               COUNT(*)   AS rows,
               MAX(date)  AS latest,
               MIN(date)  AS earliest
        FROM prices
        GROUP BY commodity
        ORDER BY commodity
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]