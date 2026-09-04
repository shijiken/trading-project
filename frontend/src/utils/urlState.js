// Keeps dashboard state in the query string so a view can be linked/shared and
// browser back/forward works — without pulling in a router for a single view.

export function readUrlState(defaults, validators = {}) {
  if (typeof window === "undefined") return defaults;

  const params = new URLSearchParams(window.location.search);
  const state = { ...defaults };

  Object.keys(defaults).forEach((key) => {
    const raw = params.get(key);
    if (raw == null) return;
    const validate = validators[key];
    const value = validate ? validate(raw) : raw;
    if (value != null) state[key] = value;
  });

  return state;
}

export function writeUrlState(state) {
  if (typeof window === "undefined" || !window.history) return;

  const params = new URLSearchParams(window.location.search);
  Object.entries(state).forEach(([key, value]) => {
    if (value == null || value === "") params.delete(key);
    else params.set(key, String(value));
  });

  const query = params.toString();
  window.history.replaceState(null, "", query ? `${window.location.pathname}?${query}` : window.location.pathname);
}
