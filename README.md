# Commodity Price Intelligence

Full-stack commodity analytics: a Python ETL pipeline pulls WTI crude, Brent crude,
natural gas, heating oil and gasoline prices from the EIA and FRED APIs into SQLite,
Prophet forecasts and an Isolation Forest anomaly detector run on top, and a React
dashboard surfaces price history, forecasts with confidence bands, and flagged anomalies.

```
backend/    FastAPI service — ETL, SQLite, ML, REST API
frontend/   Vite + React + Recharts dashboard
```

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` with your API keys ([EIA](https://www.eia.gov/opendata/register.php),
[FRED](https://fredaccount.stlouisfed.org/apikeys)):

```
EIA_API_KEY=your_key_here
FRED_API_KEY=your_key_here
```

Initialise the database and pull history:

```bash
python backfill.py
```

Run the API:

```bash
uvicorn main:app --reload      # http://localhost:8000
```

The API self-schedules: it refreshes ETL + ML caches every 6 hours (`scheduler.py`), and
warms the ML caches in the background on boot so it starts serving immediately.

### Frontend

```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

The API base URL defaults to `http://localhost:8000`; override with `VITE_API_BASE_URL`
(see `.env.example`).

## API

| Endpoint | Description |
| --- | --- |
| `GET /prices/?commodity=&start=&end=` | Raw price history |
| `GET /forecast/?commodity=&horizon=` | Prophet forecast, `horizon` in days (7–90) |
| `GET /anomalies/?commodity=&start=&end=` | Isolation Forest anomalies, worst first |
| `GET /health/` | Liveness plus per-commodity row counts and data freshness |

Commodities: `crude_oil`, `brent_crude`, `natural_gas`, `heating_oil`, `gasoline`
(plus `us_cpi` as macro context). Unknown names return 404.

Responses are gzipped, and forecast/anomaly results are served from a SQLite-backed
cache (`ml_cache`) refreshed on the 6-hour schedule, falling back to live computation
on a miss.

## Dashboard

- **KPI strip** — last price, period-over-period change, 52-week range
- **Price & Forecast** — history and forecast on one continuous axis split by a `Today`
  marker, with the 95% confidence band shaded; range presets (1M–All) plus a draggable
  brush to pan/zoom like a stock chart
- **Anomaly feed** — flagged dates sized/shaded by severity; click one to ring it on the chart
- **Compare mode** — overlay a second commodity, rebased to percent change (different
  units can't share a price axis)
- View state (`commodity`, `horizon`, `compare`) lives in the URL, so any view is linkable

## Tests

```bash
cd backend && python -m pytest        # 54 tests
cd frontend && npm test               # 36 tests
```

Both suites run on push/PR via `.github/workflows/ci.yml`. Backend tests use an isolated
temp SQLite database and mock all network calls, so they never touch the real database
or hit the EIA/FRED APIs.

## Notes on the data

The EIA spot-price series (`crude_oil`, `natural_gas`, `heating_oil`) and FRED's
`gasoline` are **weekly**; only `brent_crude` is daily. The forecaster infers each
series' cadence and steps the forecast to match — a 30-day horizon on a weekly series
yields ~5 weekly points, not 30 daily ones.
