/**
 * StatusBadge — colored status pill.
 * @param {string} status - 'active'|'inactive'|'pending'|'approved'|'rejected'|'critical'|'high'|'medium'|'low'|'info'|'delivered'|'in_transit'|'delayed'
 * @param {string} [label] - overrides the auto-capitalized status text
 */
const CONFIG = {
  active:     { bg: '#D1FAE5', color: '#065F46' },
  approved:   { bg: '#D1FAE5', color: '#065F46' },
  delivered:  { bg: '#D1FAE5', color: '#065F46' },
  good:       { bg: '#D1FAE5', color: '#065F46' },
  resolved:   { bg: '#F3F4F6', color: '#374151' },
  closed:     { bg: '#F3F4F6', color: '#374151' },
  inactive:   { bg: '#F3F4F6', color: '#6B7280' },
  pending:    { bg: '#FEF3C7', color: '#92400E' },
  in_transit: { bg: '#DBEAFE', color: '#1E40AF' },
  in_review:  { bg: '#DBEAFE', color: '#1E40AF' },
  info:       { bg: '#DBEAFE', color: '#1E40AF' },
  medium:     { bg: '#FEF9C3', color: '#854D0E' },
  high:       { bg: '#FEE2E2', color: '#991B1B' },
  delayed:    { bg: '#FEE2E2', color: '#991B1B' },
  rejected:   { bg: '#FEE2E2', color: '#991B1B' },
  critical:   { bg: '#FEE2E2', color: '#7F1D1D' },
  low:        { bg: '#FEF3C7', color: '#78350F' },
};

export default function StatusBadge({ status, label }) {
  const cfg = CONFIG[status?.toLowerCase()] || { bg: '#F3F4F6', color: '#6B7280' };
  const text = label || (status ? status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) : '—');
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 20, fontSize: 11.5, fontWeight: 600, background: cfg.bg, color: cfg.color, letterSpacing: '0.02em', whiteSpace: 'nowrap' }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: cfg.color, opacity: 0.7, flexShrink: 0 }} />
      {text}
    </span>
  );
}
