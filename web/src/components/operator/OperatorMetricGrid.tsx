interface OperatorMetricGridProps {
  metrics: Array<{ label: string; value: string; caption: string }>;
}

export function OperatorMetricGrid({ metrics }: OperatorMetricGridProps) {
  return (
    <div className="metric-grid">
      {metrics.map((metric) => (
        <div key={metric.label} className="metric-card">
          <strong>{metric.value}</strong>
          <span>{metric.label}</span>
          <small className="muted">{metric.caption}</small>
        </div>
      ))}
    </div>
  );
}

