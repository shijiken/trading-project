const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function get(path, params = {}) {
  const url = new URL(path, BASE_URL);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });

  const res = await fetch(url.toString());
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request to ${path} failed with ${res.status}`);
  }
  return res.json();
}

export function getPrices(commodity, { start, end } = {}) {
  return get("/prices/", { commodity, start, end });
}

export function getForecast(commodity, horizon = 30) {
  return get("/forecast/", { commodity, horizon });
}

export function getAnomalies(commodity, { start, end } = {}) {
  return get("/anomalies/", { commodity, start, end });
}

export function getHealth() {
  return get("/health/");
}
