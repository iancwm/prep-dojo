export function LoadingBlock() {
  return (
    <div className="section-card loading-block">
      <div className="skeleton skeleton-title" />
      <div className="skeleton skeleton-line" />
      <div className="skeleton skeleton-line" style={{ width: "72%" }} />
      <div className="skeleton skeleton-card" />
    </div>
  );
}

