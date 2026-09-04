export default function CommoditySelector({ commodities, value, onChange }) {
  return (
    <select
      className="commodity-selector"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label="Select commodity"
    >
      {commodities.map((c) => (
        <option key={c.id} value={c.id}>
          {c.label}
        </option>
      ))}
    </select>
  );
}
