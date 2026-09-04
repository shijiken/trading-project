import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import KpiStrip from "./KpiStrip";

describe("KpiStrip", () => {
  it("shows a skeleton while loading", () => {
    render(<KpiStrip prices={[]} unit="USD/barrel" loading />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows an empty state with no data", () => {
    render(<KpiStrip prices={[]} unit="USD/barrel" loading={false} />);
    expect(screen.getByText(/no data available/i)).toBeInTheDocument();
  });

  it("computes latest price, change direction, and 52-week range", () => {
    const prices = [
      { date: "2025-08-15", price: 60 },
      { date: "2026-08-01", price: 70 },
      { date: "2026-08-02", price: 77 },
    ];
    render(<KpiStrip prices={prices} unit="USD/barrel" loading={false} />);

    expect(screen.getAllByText(/77.00/).length).toBeGreaterThan(0);
    expect(screen.getByText(/\+10.00%/)).toBeInTheDocument();
    expect(screen.getByText(/60.00 — 77.00/)).toBeInTheDocument();
  });

  it("shows a down arrow when price falls", () => {
    const prices = [
      { date: "2026-08-01", price: 70 },
      { date: "2026-08-02", price: 63 },
    ];
    render(<KpiStrip prices={prices} unit="USD/barrel" loading={false} />);
    expect(screen.getByText(/▼/)).toBeInTheDocument();
  });
});
