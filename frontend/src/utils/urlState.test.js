import { describe, it, expect, beforeEach } from "vitest";
import { readUrlState, writeUrlState } from "./urlState";

const defaults = { commodity: "crude_oil", horizon: 30, compare: "" };

describe("urlState", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/");
  });

  it("returns defaults when the query string is empty", () => {
    expect(readUrlState(defaults)).toEqual(defaults);
  });

  it("reads known keys from the query string", () => {
    window.history.replaceState(null, "", "/?commodity=natural_gas&horizon=90");
    const state = readUrlState(defaults, { horizon: (raw) => Number(raw) });

    expect(state.commodity).toBe("natural_gas");
    expect(state.horizon).toBe(90);
  });

  it("falls back to the default when a validator rejects the value", () => {
    window.history.replaceState(null, "", "/?commodity=unobtainium");
    const state = readUrlState(defaults, {
      commodity: (raw) => (raw === "crude_oil" ? raw : null),
    });

    expect(state.commodity).toBe("crude_oil");
  });

  it("ignores keys that aren't part of the state shape", () => {
    window.history.replaceState(null, "", "/?evil=1");
    expect(readUrlState(defaults)).toEqual(defaults);
  });

  it("writes state to the query string", () => {
    writeUrlState({ commodity: "gasoline", horizon: 14 });
    const params = new URLSearchParams(window.location.search);

    expect(params.get("commodity")).toBe("gasoline");
    expect(params.get("horizon")).toBe("14");
  });

  it("removes empty values from the query string", () => {
    writeUrlState({ commodity: "gasoline", compare: "brent_crude" });
    writeUrlState({ compare: null });

    expect(new URLSearchParams(window.location.search).has("compare")).toBe(false);
  });
});
