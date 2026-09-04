import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import FreshnessBadge from "./FreshnessBadge";

const health = (age) => ({
  status: "ok",
  commodities: [{ commodity: "crude_oil", latest: "2026-08-28", age_days: age }],
});

describe("FreshnessBadge", () => {
  it("renders nothing without health data", () => {
    const { container } = render(<FreshnessBadge health={null} commodity="crude_oil" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing for a commodity missing from the report", () => {
    const { container } = render(<FreshnessBadge health={health(3)} commodity="natural_gas" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the data age", () => {
    render(<FreshnessBadge health={health(3)} commodity="crude_oil" />);
    expect(screen.getByText(/3 days ago/)).toBeInTheDocument();
    expect(screen.getByText(/3 days ago/).closest("span")).not.toHaveClass("stale");
  });

  it("flags data that is well past the refresh cycle as stale", () => {
    render(<FreshnessBadge health={health(40)} commodity="crude_oil" />);
    expect(screen.getByText(/stale data/i)).toBeInTheDocument();
  });
});
