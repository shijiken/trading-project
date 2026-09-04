import { useEffect, useState } from "react";
import { COMMODITIES } from "./commodities";
import { getPrices, getForecast, getAnomalies, getHealth } from "./api";
import { readUrlState, writeUrlState } from "./utils/urlState";
import CommoditySelector from "./components/CommoditySelector";
import MarketChart from "./components/MarketChart";
import AnomalyFeed from "./components/AnomalyFeed";
import KpiStrip from "./components/KpiStrip";
import Skeleton from "./components/Skeleton";
import FreshnessBadge from "./components/FreshnessBadge";

const HORIZONS = [7, 14, 30, 60, 90];

const initial = readUrlState(
  { commodity: COMMODITIES[0].id, horizon: 30, compare: "" },
  {
    commodity: (raw) => (COMMODITIES.some((c) => c.id === raw) ? raw : null),
    horizon: (raw) => (HORIZONS.includes(Number(raw)) ? Number(raw) : null),
    compare: (raw) => (COMMODITIES.some((c) => c.id === raw) ? raw : null),
  }
);

export default function App() {
  const [commodity, setCommodity] = useState(initial.commodity);
  const [horizon, setHorizon] = useState(initial.horizon);
  const [compare, setCompare] = useState(initial.compare);
  const [prices, setPrices] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [comparePrices, setComparePrices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [highlightedDate, setHighlightedDate] = useState(null);
  const [health, setHealth] = useState(null);

  const meta = COMMODITIES.find((c) => c.id === commodity);
  const compareMeta = COMMODITIES.find((c) => c.id === compare);

  // Freshness is global, not per-commodity — fetch it once.
  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null)); // non-critical: the dashboard works without it
  }, []);

  // Keep the URL in sync so the current view can be linked and shared.
  useEffect(() => {
    writeUrlState({ commodity, horizon, compare: compare || null });
  }, [commodity, horizon, compare]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setHighlightedDate(null);

    Promise.all([
      getPrices(commodity),
      getForecast(commodity, horizon),
      getAnomalies(commodity),
      compare ? getPrices(compare) : Promise.resolve([]),
    ])
      .then(([priceData, forecastData, anomalyData, compareData]) => {
        if (cancelled) return;
        setPrices(priceData);
        setForecast(forecastData);
        setAnomalies(anomalyData);
        setComparePrices(compareData);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message);
        setPrices([]);
        setForecast([]);
        setAnomalies([]);
        setComparePrices([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [commodity, horizon, compare]);

  function selectAnomaly(date) {
    setHighlightedDate((current) => (current === date ? null : date));
  }

  const comparing = Boolean(compare) && comparePrices.length > 0;

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-title">
          <h1>Commodity Intelligence</h1>
          <FreshnessBadge health={health} commodity={commodity} />
        </div>
        <div className="app-controls">
          <CommoditySelector commodities={COMMODITIES} value={commodity} onChange={setCommodity} />
          <select
            className="commodity-selector"
            value={compare}
            onChange={(e) => setCompare(e.target.value)}
            aria-label="Compare with commodity"
          >
            <option value="">Compare…</option>
            {COMMODITIES.filter((c) => c.id !== commodity).map((c) => (
              <option key={c.id} value={c.id}>
                vs {c.label}
              </option>
            ))}
          </select>
        </div>
      </header>

      {error && <div className="error-banner">Failed to load data: {error}</div>}

      <KpiStrip prices={prices} unit={meta.unit} loading={loading} />

      <main className="app-grid">
        <section className="panel panel-main">
          <h2>{comparing ? "Relative Performance" : "Price & Forecast"}</h2>
          <MarketChart
            prices={prices}
            forecast={forecast}
            unit={meta.unit}
            anomalies={anomalies}
            horizon={horizon}
            onHorizonChange={setHorizon}
            loading={loading}
            highlightedDate={highlightedDate}
            comparePrices={compare ? comparePrices : []}
            primaryLabel={meta.label}
            compareLabel={compareMeta?.label}
          />
        </section>

        <section className="panel">
          <h2>Anomaly Feed</h2>
          {loading ? (
            <Skeleton height={240} label="Loading anomalies" />
          ) : (
            <AnomalyFeed
              anomalies={anomalies}
              unit={meta.unit}
              onSelect={selectAnomaly}
              selectedDate={highlightedDate}
            />
          )}
        </section>
      </main>
    </div>
  );
}
