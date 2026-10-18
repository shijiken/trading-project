export default function AnomalyFeed({ anomalies, unit, onSelect, selectedDate }) {
  if (!anomalies || anomalies.length === 0) {
    return <p className="empty-state">No anomalies flagged for this commodity.</p>;
  }

  const maxAbsScore = Math.max(...anomalies.map((a) => Math.abs(a.score)), 0.0001);

  return (
    <ul className="anomaly-feed">
      {anomalies.map((a) => {
        const severity = Math.min(1, Math.abs(a.score) / maxAbsScore);
        return (
          <li
            key={a.date}
            className={`anomaly-row${selectedDate === a.date ? " selected" : ""}`}
            style={{ "--severity": severity }}
            onClick={() => onSelect && onSelect(a.date)}
            onKeyDown={(e) => {
              if (!onSelect) return;
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect(a.date);
              }
            }}
            role={onSelect ? "button" : undefined}
            tabIndex={onSelect ? 0 : undefined}
            aria-pressed={onSelect ? selectedDate === a.date : undefined}
          >
            <span className="anomaly-date">{a.date}</span>
            <span className="anomaly-price">
              {a.price} {unit}
            </span>
            <span className="anomaly-score" title="Isolation Forest score (more negative = more anomalous)">
              score {a.score}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
