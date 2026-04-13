from db.setup import init_db
from services.eia import fetch_all_eia
from services.fred import fetch_all_fred

if __name__ == "__main__":
    print("Initializing database...")
    init_db()

    print("\nFetching EIA data...")
    fetch_all_eia()

    print("\nFetching FRED data...")
    fetch_all_fred()

    print("\nBackfill complete.")