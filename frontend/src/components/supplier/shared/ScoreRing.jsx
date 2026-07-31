/**
 * ScoreRing — Circular SVG gauge for AI performance scores (0–100).
 * Read-only visual component.
 */
export default function ScoreRing({ score = 0, label, color = '#2563EB', size = 100, loading }) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(Math.max(score, 0), 100);
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const getColor = () => {
    if (score >= 80) return '#10B981';
    if (score >= 60) return '#F59E0B';
    if (score >= 40) return '#EF4444';
    return '#6B7280';
  };

  const ringColor = color === 'auto' ? getColor() : color;

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
        <div className="skeleton" style={{ width: size, height: size, borderRadius: '50%' }} />
        <div className="skeleton" style={{ width: 60, height: 12, borderRadius: 6 }} />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          {/* Track */}
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#F3F4F6" strokeWidth={8} />
          {/* Progress */}
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={ringColor} strokeWidth={8}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            style={{ transition: 'stroke-dashoffset 1s ease-out, stroke 0.3s' }}
          />
        </svg>
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontSize: size > 80 ? 20 : 14, fontWeight: 800, color: '#111827', lineHeight: 1 }}>{progress}</span>
          <span style={{ fontSize: 10, color: '#9CA3AF', fontWeight: 500 }}>/100</span>
        </div>
      </div>
      {label && <span style={{ fontSize: 12, fontWeight: 600, color: '#374151', textAlign: 'center' }}>{label}</span>}
    </div>
  );
}
