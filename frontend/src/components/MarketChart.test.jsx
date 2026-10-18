import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import MarketChart, { buildComparisonSeries } from "./MarketChart";

function makeDailyPrices(n) {
  const rows = [];
  const start = new Date("2024-01-01");
  for (let i = 0; i < n; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    rows.push({ date: d.toISOString().slice(0, 10), price: 70 + i * 0.1 });
  }
  return rows;
}

describe("buildComparisonSeries", () => {
  it("rebases both series to percent change from their own first value", () => {
    const primary = [
      { date: "2024-01-01", price: 100 },
      { date: "2024-01-02", price: 110 },
    ];
    const compare = [
      { date: "2024-01-01", price: 4 },
      { date: "2024-01-02", price: 3 },
    ];

    const series = buildComparisonSeries(primary, compare);

    expect(series[0].primaryPct).toBeCloseTo(0);
    expect(series[0].comparePct).toBeCloseTo(0);
    expect(series[1].primaryPct).toBeCloseTo(10);
    expect(series[1].comparePct).toBeCloseTo(-25);
  });

  it("aligns series with different observation dates, leaving gaps as null", () => {
    const primary = [
      { date: "2024-01-01", price: 100 },
      { date: "2024-01-03", price: 120 },
    ];
    const compare = [{ date: "2024-01-01", price: 50 }];

    const series = buildComparisonSeries(primary, compare);

    expect(series.map((r) => r.date)).toEqual(["2024-01-01", "2024-01-03"]);
    expect(series[1].comparePct).toBeNull();
  });

  it("returns nothing when either series is missing", () => {
    expect(buildComparisonSeries([], [{ date: "2024-01-01", price: 1 }])).toEqual([]);
    expect(buildComparisonSeries([{ date: "2024-01-01", price: 1 }], [])).toEqual([]);
  });
});

describe("MarketChart", () => {
  it("shows a skeleton while loading", () => {
    render(<MarketChart prices={[]} forecast={[]} unit="USD/barrel" anomalies={[]} horizon={30} onHorizonChange={() => {}} loading />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows an empty state when there is no price history", () => {
    render(
      <MarketChart
        prices={[]}
        forecast={[]}
        unit="USD/barrel"
        anomalies={[]}
        horizon={30}
        onHorizonChange={() => {}}
        loading={false}
      />
    );
    expect(screen.getByText(/no price history available/i)).toBeInTheDocument();
  });

  it("renders a chart container, range presets, and horizon buttons", () => {
    const { container } = render(
      <MarketChart
        prices={makeDailyPrices(400)}
        forecast={[{ date: "2025-02-05", predicted: 90, lower: 85, upper: 95 }]}
        unit="USD/barrel"
        anomalies={[]}
        horizon={30}
        onHorizonChange={() => {}}
        loading={false}
      />
    );

    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument();
    expect(container.querySelector(".recharts-brush")).toBeInTheDocument();
    ["1M", "3M", "6M", "1Y", "5Y", "All"].forEach((label) => {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    });
    ["7d", "14d", "30d", "60d", "90d"].forEach((label) => {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "30d" })).toHaveClass("active");
  });

  it("reports horizon changes", async () => {
    const onHorizonChange = vi.fn();
    render(
      <MarketChart
        prices={makeDailyPrices(60)}
        forecast={[]}
        unit="USD/barrel"
        anomalies={[]}
        horizon={30}
        onHorizonChange={onHorizonChange}
        loading={false}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "90d" }));
    expect(onHorizonChange).toHaveBeenCalledWith(90);
  });

  it("shows a legend with both commodity names in comparison mode", () => {
    render(
      <MarketChart
        prices={makeDailyPrices(30)}
        forecast={[]}
        unit="USD/barrel"
        anomalies={[]}
        horizon={30}
        onHorizonChange={() => {}}
        loading={false}
        comparePrices={makeDailyPrices(30)}
        primaryLabel="WTI Crude Oil"
        compareLabel="Natural Gas"
      />
    );

    expect(screen.getByText("WTI Crude Oil")).toBeInTheDocument();
    expect(screen.getByText("Natural Gas")).toBeInTheDocument();
    // horizon controls are irrelevant when no forecast is drawn
    expect(screen.queryByRole("button", { name: "30d" })).not.toBeInTheDocument();
  });

  it("draws a highlight ring around the selected anomaly", () => {
    const prices = makeDailyPrices(60);
    const anomalyDate = prices[30].date;
    const { container } = render(
      <MarketChart
        prices={prices}
        forecast={[]}
        unit="USD/barrel"
        anomalies={[{ date: anomalyDate, commodity: "crude_oil", price: prices[30].price, unit: "USD/barrel", score: -0.5 }]}
        horizon={30}
        onHorizonChange={() => {}}
        loading={false}
        highlightedDate={anomalyDate}
      />
    );

    expect(container.querySelector(".anomaly-highlight-ring")).toBeInTheDocument();
  });
});
