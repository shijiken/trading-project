import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import AnomalyFeed from "./AnomalyFeed";

describe("AnomalyFeed", () => {
  it("shows an empty state when there are no anomalies", () => {
    render(<AnomalyFeed anomalies={[]} unit="USD/barrel" />);
    expect(screen.getByText(/no anomalies flagged/i)).toBeInTheDocument();
  });

  it("lists each anomaly's date, price, and score", () => {
    render(
      <AnomalyFeed
        anomalies={[
          { date: "2026-03-01", commodity: "crude_oil", price: 120.5, unit: "USD/barrel", score: -0.42 },
          { date: "2026-03-15", commodity: "crude_oil", price: 15.0, unit: "USD/barrel", score: -0.31 },
        ]}
        unit="USD/barrel"
      />
    );

    expect(screen.getByText("2026-03-01")).toBeInTheDocument();
    expect(screen.getByText("2026-03-15")).toBeInTheDocument();
    expect(screen.getByText(/120.5 USD\/barrel/)).toBeInTheDocument();
    expect(screen.getByText(/score -0.42/)).toBeInTheDocument();
  });

  it("calls onSelect with the clicked anomaly's date", async () => {
    const onSelect = vi.fn();
    render(
      <AnomalyFeed
        anomalies={[{ date: "2026-03-01", commodity: "crude_oil", price: 120.5, unit: "USD/barrel", score: -0.42 }]}
        unit="USD/barrel"
        onSelect={onSelect}
      />
    );

    await userEvent.click(screen.getByText("2026-03-01"));

    expect(onSelect).toHaveBeenCalledWith("2026-03-01");
  });

  it("can be activated from the keyboard", async () => {
    const onSelect = vi.fn();
    render(
      <AnomalyFeed
        anomalies={[{ date: "2026-03-01", commodity: "crude_oil", price: 120.5, unit: "USD/barrel", score: -0.42 }]}
        unit="USD/barrel"
        onSelect={onSelect}
      />
    );

    screen.getByRole("button").focus();
    await userEvent.keyboard("{Enter}");

    expect(onSelect).toHaveBeenCalledWith("2026-03-01");
  });

  it("marks the selected row", () => {
    render(
      <AnomalyFeed
        anomalies={[{ date: "2026-03-01", commodity: "crude_oil", price: 120.5, unit: "USD/barrel", score: -0.42 }]}
        unit="USD/barrel"
        onSelect={() => {}}
        selectedDate="2026-03-01"
      />
    );

    expect(screen.getByText("2026-03-01").closest("li")).toHaveClass("selected");
  });
});
