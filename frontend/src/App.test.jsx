import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import App from "./App";

function jsonResponse(body) {
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve(body),
  });
}

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url) => {
        const href = url.toString();
        if (href.includes("/prices/")) {
          return jsonResponse([{ date: "2026-01-01", commodity: "crude_oil", price: 70, unit: "USD/barrel" }]);
        }
        if (href.includes("/forecast/")) {
          return jsonResponse([{ date: "2026-01-02", predicted: 71, lower: 66, upper: 76 }]);
        }
        if (href.includes("/anomalies/")) {
          return jsonResponse([{ date: "2026-01-01", commodity: "crude_oil", price: 70, unit: "USD/barrel", score: -0.2 }]);
        }
        if (href.includes("/health/")) {
          return jsonResponse({
            status: "ok",
            commodities: [{ commodity: "crude_oil", latest: "2026-01-01", age_days: 2 }],
          });
        }
        return jsonResponse([]);
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads and displays data for the default commodity", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: /commodity intelligence/i })).toBeInTheDocument();

    await waitFor(() => expect(screen.getByText(/score -0.2/)).toBeInTheDocument());

    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/prices/?commodity=crude_oil"));
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/forecast/?commodity=crude_oil"));
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/anomalies/?commodity=crude_oil"));
  });

  it("re-fetches when the commodity selection changes", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByText(/score -0.2/)).toBeInTheDocument());

    await userEvent.selectOptions(screen.getByRole("combobox", { name: /select commodity/i }), "brent_crude");

    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/prices/?commodity=brent_crude"))
    );
  });

  it("fetches the comparison series and switches to relative performance", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByText(/score -0.2/)).toBeInTheDocument());

    await userEvent.selectOptions(screen.getByRole("combobox", { name: /compare with commodity/i }), "brent_crude");

    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/prices/?commodity=brent_crude"))
    );
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /relative performance/i })).toBeInTheDocument()
    );
  });

  it("reflects the selected commodity in the URL for sharing", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByText(/score -0.2/)).toBeInTheDocument());

    await waitFor(() =>
      expect(new URLSearchParams(window.location.search).get("commodity")).toBe("crude_oil")
    );
  });

  it("shows the data freshness badge", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByText(/2 days ago/)).toBeInTheDocument());
  });

  it("shows an error banner when a request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 400,
          json: () => Promise.resolve({ detail: "Not enough data" }),
        })
      )
    );

    render(<App />);

    await waitFor(() => expect(screen.getByText(/failed to load data/i)).toBeInTheDocument());
    expect(screen.getByText(/not enough data/i)).toBeInTheDocument();
  });
});
