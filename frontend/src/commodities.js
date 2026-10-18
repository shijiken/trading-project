// Mirrors backend/services/eia.py EIA_SERIES and backend/services/fred.py FRED_SERIES.
// us_cpi is macro context in the backend, not shown here as a tradeable commodity.
export const COMMODITIES = [
  { id: "crude_oil", label: "WTI Crude Oil", unit: "USD/barrel" },
  { id: "brent_crude", label: "Brent Crude Oil", unit: "USD/barrel" },
  { id: "natural_gas", label: "Natural Gas (Henry Hub)", unit: "USD/MMBtu" },
  { id: "heating_oil", label: "Heating Oil (NY Harbor)", unit: "USD/gallon" },
  { id: "gasoline", label: "Gasoline", unit: "USD/gallon" },
];
