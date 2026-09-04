import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import CommoditySelector from "./CommoditySelector";

const commodities = [
  { id: "crude_oil", label: "WTI Crude Oil", unit: "USD/barrel" },
  { id: "brent_crude", label: "Brent Crude Oil", unit: "USD/barrel" },
];

describe("CommoditySelector", () => {
  it("renders one option per commodity", () => {
    render(<CommoditySelector commodities={commodities} value="crude_oil" onChange={() => {}} />);
    expect(screen.getByRole("option", { name: "WTI Crude Oil" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Brent Crude Oil" })).toBeInTheDocument();
  });

  it("calls onChange with the selected commodity id", async () => {
    const onChange = vi.fn();
    render(<CommoditySelector commodities={commodities} value="crude_oil" onChange={onChange} />);

    await userEvent.selectOptions(screen.getByRole("combobox"), "brent_crude");

    expect(onChange).toHaveBeenCalledWith("brent_crude");
  });
});
