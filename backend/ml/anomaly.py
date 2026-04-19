import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from services.db import get_prices

def detect_anomalies(commodity: str, start: str = None, end: str = None) -> list[dict]:
    """
    Fits Isolation Forest on price history,
    returns only the flagged anomalous dates.
    """
    records = get_prices(commodity, start=start, end=end)

    if len(records) < 20:
        raise ValueError(f"Not enough data to detect anomalies for {commodity}.")

    prices = np.array([r["price"] for r in records]).reshape(-1, 1)

    # Scale first — Isolation Forest is sensitive to feature scale
    scaler = StandardScaler()
    prices_scaled = scaler.fit_transform(prices)

    model = IsolationForest(
        contamination=0.05,   # expects ~5% of points to be anomalies
        n_estimators=100,
        random_state=42,
    )
    labels = model.fit_predict(prices_scaled)       # -1 = anomaly, 1 = normal
    scores = model.decision_function(prices_scaled) # lower = more anomalous

    anomalies = []
    for record, label, score in zip(records, labels, scores):
        if label == -1:
            anomalies.append({
                "date":      record["date"],
                "commodity": record["commodity"],
                "price":     record["price"],
                "unit":      record["unit"],
                "score":     round(float(score), 4),  # negative = more anomalous
            })

    return sorted(anomalies, key=lambda x: x["score"])  # worst anomalies first