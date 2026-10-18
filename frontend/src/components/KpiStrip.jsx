import { latestChange, trailingRange, formatPrice, formatPct } from "../utils/marketStats";
import Skeleton from "./Skeleton";

export default function KpiStrip({ prices, unit, loading }) {
  if (loading) return <Skeleton height={84} label="Loading price summary" />;
  if (!prices || prices.length === 0) {
    return <p className="empty-state">No data available.</p>;
  }

  const latest = prices[prices.length - 1];
  const change = latestChange(prices); // null when there's only one data point
  const range = trailingRange(prices, 365);
  const direction = change && change.delta > 0 ? "up" : change && change.delta < 0 ? "down" : "flat";

  const rangePct =
    range && range.high !== range.low ? ((latest.price - range.low) / (range.high - range.low)) * 100 : 50;

  return (
    <div className="kpi-strip">
      <div className="kpi-block">
        <span className="kpi-label">Last</span>
        <span className="kpi-value">
          {formatPrice(latest.price)} <span className="kpi-unit">{unit}</span>
        </span>
        <span className="kpi-subtext">as of {latest.date}</span>
      </div>

      <div className="kpi-block">
        <span className="kpi-label">Change</span>
        {change ? (
          <>
            <span className={`kpi-value kpi-${direction}`}>
              {direction === "up" ? "▲" : direction === "down" ? "▼" : "•"} {formatPct(change.pct)}
            </span>
            <span className="kpi-subtext">
              {formatPrice(Math.abs(change.delta))} {unit}
            </span>
          </>
        ) : (
          <span className="kpi-value">—</span>
        )}
      </div>

      {range && (
        <div className="kpi-block kpi-range">
          <span className="kpi-label">52-Week Range</span>
          <div className="kpi-range-bar">
            <div className="kpi-range-track" />
            <div className="kpi-range-marker" style={{ left: `${Math.min(100, Math.max(0, rangePct))}%` }} />
          </div>
          <span className="kpi-subtext">
            {formatPrice(range.low)} — {formatPrice(range.high)} {unit}
          </span>
        </div>
      )}
    </div>
  );
}
