import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, Globe, Calendar, ChevronDown, ExternalLink, MapPin, Users, TrendingUp, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { severityColor, statusColor, timeAgo } from '../lib/utils';

const severities = ['all', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const statuses   = ['all', 'active', 'monitoring', 'resolved'];

/* ── Skeleton ── */
function SkeletonRow() {
  return (
    <tr style={{ borderBottom: '1px solid #F9FAFB' }}>
      {Array.from({ length: 8 }).map((_, i) => (
        <td key={i} style={{ padding: '14px' }}>
          <div style={{ height: 12, background: '#F3F4F6', borderRadius: 4, width: i === 0 ? 180 : 80, animation: 'pulse 1.5s infinite' }} />
        </td>
      ))}
    </tr>
  );
}

/* ── Detail Modal ── */
function DisruptionModal({ item, onClose }) {
  const sc  = severityColor((item.risk_level || item.severity || 'medium').toLowerCase());
  const stc = statusColor('active');
  return (
    <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.96, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.96, y: 20 }}
        onClick={e => e.stopPropagation()}
        style={{ width: 580, background: 'white', borderRadius: 14, boxShadow: '0 20px 60px rgba(0,0,0,0.12)', border: '1px solid #E5E7EB', overflow: 'hidden', maxHeight: '90vh', overflowY: 'auto' }}
      >
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #F3F4F6', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <span style={{ background: sc.bg, color: sc.text, fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 10, textTransform: 'uppercase' }}>{item.risk_level || item.severity}</span>
            </div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: '#111827', marginBottom: 4 }}>{item.title}</h2>
            <div style={{ display: 'flex', gap: 12, fontSize: 12, color: '#9CA3AF' }}>
              {item.countries?.length > 0 && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><MapPin size={12} /> {item.countries.join(', ')}</span>}
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Calendar size={12} /> {timeAgo(item.assessed_at || item.published_at)}</span>
            </div>
          </div>
          <button onClick={onClose} style={{ background: '#F3F4F6', border: 'none', borderRadius: 8, width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
            <X size={16} color="#6B7280" />
          </button>
        </div>
        <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            {[
              { label: 'Risk Score',    value: `${(item.risk_score || 0).toFixed(1)}/100` },
              { label: 'Risk Level',    value: item.risk_level || '—' },
              { label: 'Confidence',    value: item.confidence_label || '—' },
            ].map(stat => (
              <div key={stat.label} style={{ background: '#FAFAFA', border: '1px solid #F3F4F6', borderRadius: 8, padding: 12, textAlign: 'center' }}>
                <div style={{ fontSize: 11, color: '#9CA3AF', marginBottom: 4 }}>{stat.label}</div>
                <div style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>{stat.value}</div>
              </div>
            ))}
          </div>
          <div style={{ flex: 1, background: '#FAFAFA', border: '1px solid #F3F4F6', borderRadius: 8, padding: 12 }}>
            <div style={{ fontSize: 11, color: '#9CA3AF', marginBottom: 4 }}>Source</div>
            <div style={{ fontSize: 13, fontWeight: 500, color: '#2563EB', display: 'flex', alignItems: 'center', gap: 4 }}>
              {item.url ? <a href={item.url} target="_blank" rel="noreferrer" style={{ color: '#2563EB', display: 'flex', alignItems: 'center', gap: 4 }}><ExternalLink size={12} /> {item.source || 'View Source'}</a> : (item.source || 'N/A')}
            </div>
          </div>
          {item.industries?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: '#9CA3AF', marginBottom: 6 }}>Industries Affected</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {item.industries.map(ind => (
                  <span key={ind} style={{ background: '#EFF6FF', color: '#1E40AF', border: '1px solid #BFDBFE', borderRadius: 6, padding: '3px 10px', fontSize: 12, fontWeight: 500 }}>{ind}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ── Main Page ── */
export default function DisruptionMonitor() {
  const [search,   setSearch]   = useState('');
  const [severity, setSeverity] = useState('all');
  const [status,   setStatus]   = useState('all');
  const [selected, setSelected] = useState(null);
  const [page,     setPage]     = useState(1);
  const PER_PAGE = 10;

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['disruption-monitor'],
    queryFn:  () => api.get('/risk/assessments'),
  });

  // Normalise API response — accept both list and {assessments: [...]} shapes
  const assessments = Array.isArray(data)
    ? data
    : Array.isArray(data?.assessments)
    ? data.assessments
    : [];

  const filtered = assessments.filter(d => {
    const lvl = (d.risk_level || '').toUpperCase();
    const matchSev = severity === 'all' || lvl === severity.toUpperCase();
    const title = (d.title || '').toLowerCase();
    const matchSearch = !search || title.includes(search.toLowerCase());
    return matchSev && matchSearch;
  });

  const totalPages = Math.ceil(filtered.length / PER_PAGE);
  const paginated  = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1200 }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Disruption Monitor</h1>
            <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Live risk assessment feed from AI Risk Agent</p>
          </div>
          <button onClick={() => refetch()} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        className="card" style={{ padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#F5F5F5', border: '1px solid #E5E7EB', borderRadius: 8, padding: '7px 12px', flex: 1, minWidth: 200 }}>
          <Search size={14} color="#9CA3AF" />
          <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Search disruptions..." style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: 13, color: '#111827', width: '100%' }} />
        </div>
        {[{ label: 'Severity', options: severities, val: severity, set: v => { setSeverity(v); setPage(1); } }].map(f => (
          <div key={f.label} style={{ position: 'relative' }}>
            <select value={f.val} onChange={e => f.set(e.target.value)}
              style={{ appearance: 'none', background: '#F5F5F5', border: '1px solid #E5E7EB', borderRadius: 8, padding: '7px 32px 7px 12px', fontSize: 13, color: '#374151', cursor: 'pointer', outline: 'none' }}>
              {f.options.map(o => <option key={o} value={o}>{o === 'all' ? 'All Severities' : o}</option>)}
            </select>
            <ChevronDown size={13} color="#9CA3AF" style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
          </div>
        ))}
        {(search || severity !== 'all') && (
          <button onClick={() => { setSearch(''); setSeverity('all'); setPage(1); }}
            style={{ display: 'flex', alignItems: 'center', gap: 4, background: '#FEE2E2', color: '#DC2626', border: 'none', borderRadius: 8, padding: '7px 12px', fontSize: 13, cursor: 'pointer', fontWeight: 500 }}>
            <X size={13} /> Clear
          </button>
        )}
        <span style={{ marginLeft: 'auto', fontSize: 12, color: '#9CA3AF' }}>{isLoading ? '...' : `${filtered.length} events`}</span>
      </motion.div>

      {/* Error */}
      {isError && (
        <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, padding: '12px 16px', fontSize: 13, color: '#991B1B' }}>
          Failed to load disruption data from backend. Make sure the backend server is running.
        </div>
      )}

      {/* Table */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="card" style={{ overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #F3F4F6', background: '#FAFAFA' }}>
                {['Event', 'Countries', 'Severity', 'Risk Score', 'Trajectory', 'Industries', 'Time', ''].map(h => (
                  <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)
                : paginated.map((d, i) => {
                    const sc = severityColor((d.risk_level || 'medium').toLowerCase());
                    return (
                      <motion.tr key={d.assessment_id || i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                        style={{ borderBottom: '1px solid #F9FAFB', cursor: 'pointer', transition: 'background 0.1s' }}
                        onMouseEnter={e => e.currentTarget.style.background = '#FAFAFA'}
                        onMouseLeave={e => e.currentTarget.style.background = 'white'}
                        onClick={() => setSelected(d)}
                      >
                        <td style={{ padding: '12px 14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div style={{ width: 8, height: 8, borderRadius: '50%', background: sc.dot, flexShrink: 0 }} />
                            <div>
                              <div style={{ fontSize: 13, fontWeight: 500, color: '#111827', maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.title || 'Unnamed Event'}</div>
                              <div style={{ fontSize: 11, color: '#9CA3AF' }}>{d.source || d.event_type || '—'}</div>
                            </div>
                          </div>
                        </td>
                        <td style={{ padding: '12px 14px', fontSize: 12.5, color: '#6B7280' }}>{(d.countries || []).slice(0, 2).join(', ') || 'Global'}</td>
                        <td style={{ padding: '12px 14px' }}>
                          <span style={{ background: sc.bg, color: sc.text, fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 10, textTransform: 'uppercase' }}>{d.risk_level}</span>
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <div style={{ width: 50, height: 5, background: '#F3F4F6', borderRadius: 3, overflow: 'hidden' }}>
                              <div style={{ width: `${d.risk_score || 0}%`, height: '100%', background: (d.risk_score || 0) > 80 ? '#DC2626' : (d.risk_score || 0) > 60 ? '#D97706' : '#059669', borderRadius: 3 }} />
                            </div>
                            <span style={{ fontSize: 12, fontWeight: 600, color: (d.risk_score || 0) > 80 ? '#DC2626' : (d.risk_score || 0) > 60 ? '#D97706' : '#059669' }}>{(d.risk_score || 0).toFixed(0)}</span>
                          </div>
                        </td>
                        <td style={{ padding: '12px 14px', fontSize: 12, color: '#6B7280' }}>{d.trajectory || '—'}</td>
                        <td style={{ padding: '12px 14px', fontSize: 12, color: '#6B7280' }}>{(d.industries || []).slice(0, 2).join(', ') || '—'}</td>
                        <td style={{ padding: '12px 14px', fontSize: 12, color: '#9CA3AF', whiteSpace: 'nowrap' }}>{timeAgo(d.assessed_at)}</td>
                        <td style={{ padding: '12px 14px' }}>
                          <button onClick={e => { e.stopPropagation(); setSelected(d); }} style={{ background: '#EFF6FF', color: '#2563EB', border: 'none', borderRadius: 6, padding: '5px 10px', fontSize: 12, cursor: 'pointer', fontWeight: 500 }}>Details</button>
                        </td>
                      </motion.tr>
                    );
                  })}
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ padding: '12px 16px', borderTop: '1px solid #F3F4F6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: '#9CA3AF' }}>Showing {(page - 1) * PER_PAGE + 1}–{Math.min(page * PER_PAGE, filtered.length)} of {filtered.length}</span>
            <div style={{ display: 'flex', gap: 6 }}>
              {Array.from({ length: totalPages }, (_, i) => (
                <button key={i} onClick={() => setPage(i + 1)} style={{ width: 30, height: 30, borderRadius: 6, border: '1px solid', borderColor: page === i + 1 ? '#2563EB' : '#E5E7EB', background: page === i + 1 ? '#EFF6FF' : 'white', color: page === i + 1 ? '#2563EB' : '#6B7280', fontSize: 13, fontWeight: page === i + 1 ? 700 : 400, cursor: 'pointer' }}>
                  {i + 1}
                </button>
              ))}
            </div>
          </div>
        )}
      </motion.div>

      <AnimatePresence>
        {selected && <DisruptionModal item={selected} onClose={() => setSelected(null)} />}
      </AnimatePresence>
    </div>
  );
}
