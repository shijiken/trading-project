// Derived stats for the KPI strip — all computed client-side from the same
// /prices history the chart already has, no extra network round trip.

export function latestChange(prices) {
  if (!prices || prices.length < 2) return null;
  const last = prices[prices.length - 1];
  const prev = prices[prices.length - 2];
  const delta = last.price - prev.price;
  const pct = prev.price !== 0 ? (delta / prev.price) * 100 : 0;
  return { latest: last.price, delta, pct, asOf: last.date };
}

export function trailingRange(prices, days = 365) {
  if (!prices || prices.length === 0) return null;
  const lastDate = new Date(prices[prices.length - 1].date);
  const cutoff = new Date(lastDate);
  cutoff.setDate(cutoff.getDate() - days);
  const window = prices.filter((p) => new Date(p.date) >= cutoff);
  const values = (window.length ? window : prices).map((p) => p.price);
  return { low: Math.min(...values), high: Math.max(...values) };
}

export function formatPrice(value, digits = 2) {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function formatPct(value, digits = 2) {
  if (value == null || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

export function timeAgo(dateStr) {
  if (!dateStr) return "unknown";
  const then = new Date(dateStr).getTime();
  const days = Math.floor((Date.now() - then) / 86400000);
  if (days <= 0) return "today";
  if (days === 1) return "1 day ago";
  return `${days} days ago`;
}
