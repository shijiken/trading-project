import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceDot,
  ReferenceLine,
  Brush,
} from "recharts";
import Skeleton from "./Skeleton";

const RANGE_PRESETS = [
  { label: "1M", months: 1 },
  { label: "3M", months: 3 },
  { label: "6M", months: 6 },
  { label: "1Y", months: 12 },
  { label: "5Y", months: 60 },
  { label: "All", months: null },
];

const HORIZON_OPTIONS = [7, 14, 30, 60, 90];

function startIndexForPreset(rows, referenceDate, months) {
  if (months == null) return 0;
  const cutoff = new Date(referenceDate);
  cutoff.setMonth(cutoff.getMonth() - months);
  const cutoffStr = cutoff.toISOString().slice(0, 10);
  const idx = rows.findIndex((r) => r.date >= cutoffStr);
  return idx === -1 ? 0 : idx;
}

// Merge historical prices and the forecast horizon into one series so the
// chart reads as a single continuous line, with the forecast picking up
// exactly where history ends (a "bridge" point carries the last known price
// into the predicted/band fields so there's no visual gap).
function buildSeries(prices, forecast) {
  if (!prices || prices.length === 0) return [];
  const rows = prices.map((p, i) => ({
    date: p.date,
    price: p.price,
    // period-over-period move, surfaced in the tooltip
    changePct: i > 0 && prices[i - 1].price ? ((p.price - prices[i - 1].price) / prices[i - 1].price) * 100 : null,
  }));

  if (forecast && forecast.length > 0) {
    const lastHistorical = prices[prices.length - 1];
    rows[rows.length - 1] = {
      ...rows[rows.length - 1],
      predicted: lastHistorical.price,
      lower: lastHistorical.price,
      bandWidth: 0,
    };
    forecast.forEach((f) => {
      rows.push({ date: f.date, predicted: f.predicted, lower: f.lower, bandWidth: f.upper - f.lower });
    });
  }
  return rows;
}

// Two commodities can't share a price axis (USD/barrel vs USD/MMBtu), so
// comparison mode rebases both to percent change from their first observation.
export function buildComparisonSeries(primary, compare) {
  if (!primary || primary.length === 0 || !compare || compare.length === 0) return [];

  const primaryBase = primary[0].price;
  const compareBase = compare[0].price;
  if (!primaryBase || !compareBase) return [];

  const primaryByDate = new Map(primary.map((p) => [p.date, p.price]));
  const compareByDate = new Map(compare.map((p) => [p.date, p.price]));
  const dates = Array.from(new Set([...primaryByDate.keys(), ...compareByDate.keys()])).sort();

  return dates.map((date) => ({
    date,
    primaryPct: primaryByDate.has(date) ? (primaryByDate.get(date) / primaryBase - 1) * 100 : null,
    comparePct: compareByDate.has(date) ? (compareByDate.get(date) / compareBase - 1) * 100 : null,
  }));
}

function ChartTooltip({ active, payload, label, unit, comparing, primaryLabel, compareLabel }) {
  if (!active || !payload || payload.length === 0) return null;

  const row = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-date">{label}</div>
      {comparing ? (
        <>
          {row.primaryPct != null && (
            <div>
              <span className="chart-tooltip-key">{primaryLabel}</span> {row.primaryPct >= 0 ? "+" : ""}
              {row.primaryPct.toFixed(2)}%
            </div>
          )}
          {row.comparePct != null && (
            <div>
              <span className="chart-tooltip-key">{compareLabel}</span> {row.comparePct >= 0 ? "+" : ""}
              {row.comparePct.toFixed(2)}%
            </div>
          )}
        </>
      ) : (
        <>
          {row.price != null && (
            <div>
              <span className="chart-tooltip-key">Price</span> {row.price} {unit}
              {row.changePct != null && (
                <span className={row.changePct >= 0 ? "chart-tooltip-up" : "chart-tooltip-down"}>
                  {" "}
                  ({row.changePct >= 0 ? "+" : ""}
                  {row.changePct.toFixed(2)}%)
                </span>
              )}
            </div>
          )}
          {row.predicted != null && row.price == null && (
            <>
              <div>
                <span className="chart-tooltip-key">Forecast</span> {row.predicted} {unit}
              </div>
              <div className="chart-tooltip-band">
                95% CI: {row.lower?.toFixed(2)} – {(row.lower + row.bandWidth)?.toFixed(2)}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

export default function MarketChart({
  prices,
  forecast,
  unit,
  anomalies,
  horizon,
  onHorizonChange,
  loading,
  highlightedDate,
  comparePrices,
  primaryLabel,
  compareLabel,
}) {
  const [range, setRange] = useState(null);
  const [activePreset, setActivePreset] = useState("1Y");

  const comparing = Boolean(comparePrices && comparePrices.length > 0);

  const series = useMemo(
    () => (comparing ? buildComparisonSeries(prices, comparePrices) : buildSeries(prices, forecast)),
    [prices, forecast, comparePrices, comparing]
  );
  const todayDate = prices && prices.length ? prices[prices.length - 1].date : null;

  const anomalyPoints = useMemo(() => {
    if (!anomalies || anomalies.length === 0 || !prices || prices.length === 0) return [];
    const byDate = new Map(anomalies.map((a) => [a.date, a]));
    const maxAbsScore = Math.max(...anomalies.map((a) => Math.abs(a.score)), 0.0001);
    return prices
      .filter((p) => byDate.has(p.date))
      .map((p) => {
        const a = byDate.get(p.date);
        const severity = Math.min(1, Math.abs(a.score) / maxAbsScore);
        return { ...p, severity };
      });
  }, [prices, anomalies]);

  useEffect(() => {
    if (series.length === 0 || !todayDate) {
      setRange(null);
      return;
    }
    const preset = RANGE_PRESETS.find((p) => p.label === activePreset) || RANGE_PRESETS[RANGE_PRESETS.length - 1];
    setRange({ startIndex: startIndexForPreset(series, todayDate, preset.months), endIndex: series.length - 1 });
    // Reset the window only when the underlying series changes (commodity/horizon switch),
    // not on every brush drag.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [series]);

  if (loading) return <Skeleton height={400} label="Loading price and forecast chart" />;

  if (!series || series.length === 0) {
    return <p className="empty-state">No price history available for this commodity.</p>;
  }

  function applyPreset(preset) {
    setActivePreset(preset.label);
    setRange({ startIndex: startIndexForPreset(series, todayDate, preset.months), endIndex: series.length - 1 });
  }

  return (
    <div>
      <div className="chart-controls">
        <div className="range-presets">
          {RANGE_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              className={`range-preset-btn${activePreset === preset.label ? " active" : ""}`}
              onClick={() => applyPreset(preset)}
            >
              {preset.label}
            </button>
          ))}
        </div>
        {comparing ? (
          <div className="chart-legend">
            <span className="chart-legend-item">
              <span className="chart-legend-swatch" style={{ background: "var(--accent)" }} />
              {primaryLabel}
            </span>
            <span className="chart-legend-item">
              <span className="chart-legend-swatch" style={{ background: "var(--accent-2)" }} />
              {compareLabel}
            </span>
          </div>
        ) : (
          <div className="range-presets">
            <span className="chart-controls-label">Forecast</span>
            {HORIZON_OPTIONS.map((h) => (
              <button
                key={h}
                type="button"
                className={`range-preset-btn${horizon === h ? " active" : ""}`}
                onClick={() => onHorizonChange(h)}
              >
                {h}d
              </button>
            ))}
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={series} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" />
          <XAxis dataKey="date" tick={{ fill: "var(--text-muted)", fontSize: 12 }} minTickGap={40} />
          <YAxis
            tick={{ fill: "var(--text-muted)", fontSize: 12 }}
            domain={["auto", "auto"]}
            tickFormatter={comparing ? (v) => `${v.toFixed(0)}%` : undefined}
            label={{
              value: comparing ? `% since ${series[0]?.date ?? ""}` : unit,
              angle: -90,
              position: "insideLeft",
              fill: "var(--text-muted)",
            }}
          />
          <Tooltip
            content={
              <ChartTooltip
                unit={unit}
                comparing={comparing}
                primaryLabel={primaryLabel}
                compareLabel={compareLabel}
              />
            }
          />

          {!comparing && todayDate && forecast && forecast.length > 0 && (
            <ReferenceLine x={todayDate} stroke="var(--text-muted)" strokeDasharray="4 4" label={{ value: "Today", fill: "var(--text-muted)", fontSize: 11, position: "insideTopLeft" }} />
          )}

          {!comparing && (
            <Area
              dataKey="lower"
              stackId="band"
              stroke="none"
              fill="transparent"
              isAnimationActive={false}
              legendType="none"
              tooltipType="none"
            />
          )}
          {!comparing && (
            <Area
              dataKey="bandWidth"
              stackId="band"
              stroke="none"
              fill="var(--accent-2)"
              fillOpacity={0.15}
              isAnimationActive={false}
              legendType="none"
              tooltipType="none"
            />
          )}

          {comparing ? (
            <Line
              type="monotone"
              dataKey="primaryPct"
              stroke="var(--accent)"
              dot={false}
              strokeWidth={2}
              connectNulls
              isAnimationActive={false}
            />
          ) : (
            <Line type="monotone" dataKey="price" stroke="var(--accent)" dot={false} strokeWidth={2} isAnimationActive={false} />
          )}
          {comparing ? (
            <Line
              type="monotone"
              dataKey="comparePct"
              stroke="var(--accent-2)"
              dot={false}
              strokeWidth={2}
              connectNulls
              isAnimationActive={false}
            />
          ) : (
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="var(--accent-2)"
              strokeDasharray="5 4"
              dot={false}
              strokeWidth={2}
              isAnimationActive={false}
            />
          )}

          {!comparing && anomalyPoints.map((p) => (
            <ReferenceDot
              key={p.date}
              x={p.date}
              y={p.price}
              r={3 + p.severity * 6}
              fill="var(--danger)"
              fillOpacity={0.35 + p.severity * 0.5}
              stroke="var(--danger)"
            />
          ))}

          {!comparing &&
            highlightedDate &&
            anomalyPoints
              .filter((p) => p.date === highlightedDate)
              .map((p) => (
                <ReferenceDot
                  key={`highlight-${p.date}`}
                  x={p.date}
                  y={p.price}
                  r={10 + p.severity * 6}
                  fill="none"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  className="anomaly-highlight-ring"
                />
              ))}

          {range && (
            <Brush
              dataKey="date"
              height={30}
              travellerWidth={10}
              startIndex={range.startIndex}
              endIndex={range.endIndex}
              stroke="var(--accent)"
              fill="var(--bg)"
              tickFormatter={() => ""}
              onChange={(next) => {
                if (!next) return;
                setActivePreset(null);
                setRange(next);
              }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
