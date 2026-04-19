import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "commodity.db")

def init_db(path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date      TEXT NOT NULL,
            commodity TEXT NOT NULL,
            price     REAL NOT NULL,
            unit      TEXT NOT NULL,
            source    TEXT NOT NULL,
            UNIQUE(date, commodity, source)
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_commodity_date
        ON prices(commodity, date)
    """)

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()