/**
 * ProgressRing — thin circular progress ring for capacity/utilization displays.
 * Lighter than ScoreRing — no label or score text inside.
 * @param {number} value - 0 to 100
 * @param {string} [color]
 * @param {number} [size=64]
 * @param {number} [stroke=6]
 */
export function ProgressRing({ value = 0, color = '#2563EB', size = 64, stroke = 6 }) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(100, Math.max(0, value)) / 100) * circ;

  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#F3F4F6" strokeWidth={stroke} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round"
        strokeDasharray={circ} strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
      />
    </svg>
  );
}

/**
 * ProgressBar — horizontal progress bar.
 * @param {number} value - 0 to 100
 * @param {string} [color]
 * @param {string} [height='6px']
 */
export function ProgressBar({ value = 0, color = '#2563EB', height = '6px' }) {
  return (
    <div style={{ height, borderRadius: 3, background: '#F3F4F6', overflow: 'hidden' }}>
      <div style={{ width: `${Math.min(100, Math.max(0, value))}%`, height: '100%', background: color, borderRadius: 3, transition: 'width 0.6s ease-out' }} />
    </div>
  );
}
