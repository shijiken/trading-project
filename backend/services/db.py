import sqlite3

DB_PATH = "commodity.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn

def insert_prices(records: list[dict]):
    """
    records: list of {date, commodity, price, unit, source}
    Skips duplicates silently via INSERT OR IGNORE.
    """
    conn = get_conn()
    conn.executemany("""
        INSERT OR IGNORE INTO prices (date, commodity, price, unit, source)
        VALUES (:date, :commodity, :price, :unit, :source)
    """, records)
    conn.commit()
    inserted = conn.total_changes
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