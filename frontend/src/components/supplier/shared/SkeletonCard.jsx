/** SkeletonCard — shimmer placeholder matching a card shape */
export function SkeletonCard({ rows = 3, height }) {
  return (
    <div className="card" style={{ padding: '20px 24px', height }}>
      <div className="skeleton" style={{ width: 40, height: 40, borderRadius: 10, marginBottom: 16 }} />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton" style={{ width: i === 0 ? '75%' : i === 1 ? '55%' : '40%', height: 12, borderRadius: 6, marginBottom: 8 }} />
      ))}
    </div>
  );
}

/** SkeletonTable — shimmer rows for table loading state */
export function SkeletonTable({ rows = 5, cols = 4 }) {
  return (
    <div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} style={{ display: 'flex', gap: 16, padding: '12px 0', borderBottom: '1px solid #F3F4F6' }}>
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className="skeleton" style={{ flex: 1, height: 12, borderRadius: 6 }} />
          ))}
        </div>
      ))}
    </div>
  );
}

/** SkeletonLine — single shimmer text line */
export function SkeletonLine({ width = '100%', height = 12 }) {
  return <div className="skeleton" style={{ width, height, borderRadius: 6 }} />;
}
