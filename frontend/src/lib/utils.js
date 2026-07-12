export function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

export function severityColor(severity) {
  switch (severity) {
    case 'critical': return { bg: '#FEE2E2', text: '#991B1B', border: '#FCA5A5', dot: '#DC2626' };
    case 'high':     return { bg: '#FEF3C7', text: '#92400E', border: '#FCD34D', dot: '#D97706' };
    case 'medium':   return { bg: '#FEF9C3', text: '#854D0E', border: '#FDE047', dot: '#CA8A04' };
    case 'low':      return { bg: '#D1FAE5', text: '#065F46', border: '#6EE7B7', dot: '#059669' };
    default:         return { bg: '#F3F4F6', text: '#374151', border: '#D1D5DB', dot: '#9CA3AF' };
  }
}

export function statusColor(status) {
  switch (status) {
    case 'active':     return { bg: '#FEE2E2', text: '#991B1B' };
    case 'monitoring': return { bg: '#FEF3C7', text: '#92400E' };
    case 'resolved':   return { bg: '#D1FAE5', text: '#065F46' };
    case 'escalated':  return { bg: '#EDE9FE', text: '#5B21B6' };
    default:           return { bg: '#F3F4F6', text: '#374151' };
  }
}

export function agentStatusColor(status) {
  switch (status) {
    case 'running':   return { bg: '#DBEAFE', text: '#1E40AF', dot: '#2563EB' };
    case 'completed': return { bg: '#D1FAE5', text: '#065F46', dot: '#059669' };
    case 'failed':    return { bg: '#FEE2E2', text: '#991B1B', dot: '#DC2626' };
    case 'retrying':  return { bg: '#FEF3C7', text: '#92400E', dot: '#D97706' };
    case 'idle':      return { bg: '#F3F4F6', text: '#6B7280', dot: '#9CA3AF' };
    default:          return { bg: '#F3F4F6', text: '#6B7280', dot: '#9CA3AF' };
  }
}

export function formatDate(isoString) {
  const d = new Date(isoString);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function timeAgo(isoString) {
  const now = new Date();
  const d = new Date(isoString);
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60)   return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

export function scoreColor(score) {
  if (score >= 80) return '#059669';
  if (score >= 60) return '#D97706';
  if (score >= 40) return '#DC2626';
  return '#991B1B';
}

export function riskScoreColor(score) {
  if (score >= 80) return { color: '#991B1B', bg: '#FEE2E2' };
  if (score >= 60) return { color: '#92400E', bg: '#FEF3C7' };
  if (score >= 40) return { color: '#854D0E', bg: '#FEF9C3' };
  return { color: '#065F46', bg: '#D1FAE5' };
}
