// Weekly series legitimately run up to ~7 days behind; beyond two cycles
// something in the ETL is probably wrong, so surface it.
const STALE_AFTER_DAYS = 15;

export default function FreshnessBadge({ health, commodity }) {
  if (!health || !health.commodities) return null;

  const entry = health.commodities.find((c) => c.commodity === commodity);
  if (!entry || entry.age_days == null) return null;

  const stale = entry.age_days > STALE_AFTER_DAYS;
  const ageLabel =
    entry.age_days === 0 ? "today" : entry.age_days === 1 ? "1 day ago" : `${entry.age_days} days ago`;

  return (
    <span className={`freshness-badge${stale ? " stale" : ""}`} title={`Latest observation: ${entry.latest}`}>
      <span className="freshness-dot" />
      {stale ? "Stale data — " : "Data "}
      {ageLabel}
    </span>
  );
}
