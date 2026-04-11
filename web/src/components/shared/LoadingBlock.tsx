interface LoadingBlockProps {
  label?: string;
}

export function LoadingBlock({ label = "Loading" }: LoadingBlockProps) {
  return (
    <div className="section-card loading-block">
      <div className="loading-block__label">{label}</div>
      <div className="skeleton skeleton-title" />
      <div className="skeleton skeleton-line" />
      <div className="skeleton skeleton-line" style={{ width: "72%" }} />
      <div className="skeleton skeleton-card" />
    </div>
  );
}
