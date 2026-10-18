// Shimmering placeholder shaped like the content it stands in for, so panels
// don't collapse to a bare "Loading..." line and headers/controls stay put.
export default function Skeleton({ height = 320, label }) {
  return (
    <div className="skeleton" style={{ height }} role="status" aria-label={label || "Loading"}>
      <div className="skeleton-shimmer" />
    </div>
  );
}
