import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Download, Search, Zap, CheckCircle, Loader, Eye,
  AlertCircle, X, RefreshCw, ChevronRight, Activity, Shield,
  Package, Building2, BarChart3, Flame, Clock
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { formatDate, timeAgo } from '../lib/utils';

// ── Type configuration ──────────────────────────────────────────────────────

const TYPE_CONFIG = {
  executive: { bg: '#EDE9FE', text: '#5B21B6', border: '#C4B5FD', icon: BarChart3, label: 'Executive' },
  risk:      { bg: '#FEE2E2', text: '#991B1B', border: '#FCA5A5', icon: Flame,     label: 'Risk' },
  supplier:  { bg: '#DBEAFE', text: '#1E40AF', border: '#93C5FD', icon: Building2, label: 'Supplier' },
  inventory: { bg: '#D1FAE5', text: '#065F46', border: '#6EE7B7', icon: Package,   label: 'Inventory' },
  incident:  { bg: '#FEF3C7', text: '#92400E', border: '#FDE68A', icon: AlertCircle, label: 'Incident' },
};

// ── Report Preview Modal ────────────────────────────────────────────────────

function ReportModal({ reportId, onClose }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['report-data', reportId],
    queryFn: () => api.get(`/reports/${reportId}/data`),
    enabled: !!reportId,
  });

  function downloadJSON() {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = `report-${reportId?.slice(0, 8)}.json`; a.click();
    URL.revokeObjectURL(url);
  }

  function downloadCSV() {
    if (!data) return;
    const risks = data.risk_assessments || [];
    const rows  = [['Title', 'Risk Level', 'Risk Score', 'Countries', 'Assessed At']];
    risks.forEach(r => rows.push([r.title, r.risk_level, r.risk_score, (r.countries || []).join('; '), r.assessed_at]));
    const csv  = rows.map(r => r.map(v => `"${String(v || '').replace(/"/g,'""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = `report-${reportId?.slice(0, 8)}.csv`; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      onClick={onClose}
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(4px)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <motion.div initial={{ opacity: 0, y: 24, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 24 }}
        onClick={e => e.stopPropagation()}
        style={{ background: 'white', borderRadius: 18, width: '100%', maxWidth: 720, maxHeight: '85vh', overflow: 'hidden', boxShadow: '0 32px 80px rgba(0,0,0,0.18)', display: 'flex', flexDirection: 'column' }}>

        {/* Header */}
        <div style={{ padding: '20px 28px', borderBottom: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 40, height: 40, background: '#EDE9FE', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileText size={18} color="#7C3AED" />
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>Report Preview</div>
              <div style={{ fontSize: 12, color: '#9CA3AF' }}>{reportId?.slice(0, 16)}…</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={downloadCSV} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12, fontWeight: 600, background: 'white', cursor: 'pointer', color: '#374151' }}>
              <Download size={13} /> CSV
            </button>
            <button onClick={downloadJSON} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 600, background: '#111827', cursor: 'pointer', color: 'white' }}>
              <Download size={13} /> JSON
            </button>
            <button onClick={onClose} style={{ width: 34, height: 34, border: 'none', borderRadius: 8, background: '#F3F4F6', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <X size={16} color="#6B7280" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 28px' }}>
          {isLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 200, color: '#9CA3AF', gap: 10 }}>
              <Loader size={24} color="#9CA3AF" className="animate-spin" />
              <span style={{ fontSize: 13 }}>Loading report data…</span>
            </div>
          ) : isError || !data ? (
            <div style={{ textAlign: 'center', color: '#EF4444', padding: 40, fontSize: 14 }}>
              Failed to load report. Please try again.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

              {/* Summary */}
              <div style={{ background: '#F9FAFB', borderRadius: 12, padding: '16px 20px', border: '1px solid #F3F4F6' }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>AI Summary</div>
                <p style={{ fontSize: 13.5, color: '#374151', lineHeight: 1.7, margin: 0 }}>{data.summary}</p>
              </div>

              {/* KPI row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                {[
                  { label: 'News Events',     value: data.news_count,    color: '#2563EB' },
                  { label: 'Risk Assessments', value: data.risk_count,   color: '#DC2626' },
                  { label: 'Recommendations',  value: data.rec_count,    color: '#059669' },
                ].map(({ label, value, color }) => (
                  <div key={label} style={{ background: 'white', border: '1px solid #F3F4F6', borderRadius: 10, padding: '14px 16px', textAlign: 'center' }}>
                    <div style={{ fontSize: 26, fontWeight: 800, color }}>{value || 0}</div>
                    <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 4 }}>{label}</div>
                  </div>
                ))}
              </div>

              {/* Risk Assessments */}
              {(data.risk_assessments || []).length > 0 && (
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Shield size={14} color="#DC2626" /> Risk Assessments ({data.risk_assessments.length})
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {data.risk_assessments.map((r, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: '#F9FAFB', borderRadius: 8, fontSize: 13 }}>
                        <span style={{ color: '#374151', fontWeight: 500 }}>{r.title || 'Unnamed Risk'}</span>
                        <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 6,
                          background: r.risk_level === 'CRITICAL' ? '#FEE2E2' : r.risk_level === 'HIGH' ? '#FEF3C7' : '#F3F4F6',
                          color: r.risk_level === 'CRITICAL' ? '#DC2626' : r.risk_level === 'HIGH' ? '#D97706' : '#6B7280' }}>
                          {r.risk_level || 'MEDIUM'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {(data.recommendations || []).length > 0 && (
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Activity size={14} color="#059669" /> Recommendations ({data.recommendations.length})
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {data.recommendations.map((r, i) => (
                      <div key={i} style={{ padding: '10px 14px', background: '#F9FAFB', borderRadius: 8, fontSize: 13, color: '#374151', lineHeight: 1.5 }}>
                        {r.summary || `${r.recommendation_type || 'Recommendation'} — Priority: ${r.priority_score || '—'}`}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

// ── Report Card ─────────────────────────────────────────────────────────────

function ReportCard({ report, index, onPreview }) {
  const tc  = TYPE_CONFIG[report.type] || TYPE_CONFIG.executive;
  const Icon = tc.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.06 }}
      className="card"
      style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14, cursor: 'default', transition: 'transform 0.15s, box-shadow 0.15s' }}
      onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = '0 8px 30px rgba(0,0,0,0.08)'; }}
      onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = ''; }}
    >
      {/* Top row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ width: 42, height: 42, background: tc.bg, border: `1px solid ${tc.border}`, borderRadius: 11, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon size={19} color={tc.text} />
        </div>
        <span style={{ background: tc.bg, color: tc.text, border: `1px solid ${tc.border}`, fontSize: 10.5, fontWeight: 700, padding: '3px 9px', borderRadius: 20, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          {tc.label}
        </span>
      </div>

      {/* Title + meta */}
      <div>
        <div style={{ fontSize: 13.5, fontWeight: 700, color: '#111827', marginBottom: 5, lineHeight: 1.4 }}>{report.title}</div>
        <div style={{ fontSize: 11.5, color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: 5 }}>
          <Clock size={11} />
          {report.generated_at ? timeAgo(report.generated_at) : '—'}
        </div>
      </div>

      {/* Status + metrics */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, flexWrap: 'wrap' }}>
        {report.status === 'ready' ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#059669', fontWeight: 600 }}>
            <CheckCircle size={13} /> Ready
          </span>
        ) : report.status === 'generating' ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#D97706', fontWeight: 600 }}>
            <Loader size={13} className="animate-spin-slow" /> Generating…
          </span>
        ) : report.status === 'failed' ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#EF4444', fontWeight: 600 }}>
            <AlertCircle size={13} /> Failed
          </span>
        ) : null}
        {report.agent_count > 0 && (
          <span style={{ color: '#9CA3AF' }}>· {report.agent_count} agent{report.agent_count !== 1 ? 's' : ''}</span>
        )}
      </div>

      {/* Mini summary */}
      {report.summary && (
        <p style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.6, margin: 0, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {report.summary}
        </p>
      )}

      {/* Actions */}
      {report.status === 'ready' && (
        <div style={{ display: 'flex', gap: 8, marginTop: 2 }}>
          <button
            onClick={() => onPreview(report.execution_id || report.id)}
            style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 8, padding: '8px 10px', fontSize: 12, fontWeight: 600, cursor: 'pointer', transition: 'background 0.15s' }}
            onMouseEnter={e => e.currentTarget.style.background = '#DBEAFE'}
            onMouseLeave={e => e.currentTarget.style.background = '#EFF6FF'}
          >
            <Eye size={13} /> Preview
          </button>
          <button
            onClick={() => onPreview(report.execution_id || report.id)}
            style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5, background: '#111827', color: 'white', border: 'none', borderRadius: 8, padding: '8px 10px', fontSize: 12, fontWeight: 600, cursor: 'pointer', transition: 'background 0.15s' }}
            onMouseEnter={e => e.currentTarget.style.background = '#374151'}
            onMouseLeave={e => e.currentTarget.style.background = '#111827'}
          >
            <Download size={13} /> Export
          </button>
        </div>
      )}
    </motion.div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

export default function Reports() {
  const [search, setSearch]         = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [previewId, setPreviewId]   = useState(null);
  const queryClient = useQueryClient();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['reports-list', typeFilter],
    queryFn:  () => api.get(`/reports?limit=30${typeFilter !== 'all' ? '&type_filter=' + typeFilter : ''}`),
    staleTime: 30_000,
  });

  const generateMutation = useMutation({
    mutationFn: () => api.post('/reports/generate'),
    onSuccess:  () => {
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['reports-list'] });
        refetch();
      }, 1500);
    },
  });

  const reports = Array.isArray(data?.reports) ? data.reports : [];

  const filtered = reports.filter(r =>
    r.title.toLowerCase().includes(search.toLowerCase()) ||
    (r.summary || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 1280 }}>

      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Reports Center</h1>
          <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>
            AI-generated supply chain intelligence reports — {data?.total ?? 0} total
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => refetch()}
            style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '9px 14px', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 13, fontWeight: 500, background: 'white', cursor: 'pointer', color: '#374151' }}>
            <RefreshCw size={13} /> Refresh
          </button>
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '9px 16px', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 700, background: generateMutation.isPending ? '#9CA3AF' : '#111827', color: 'white', cursor: generateMutation.isPending ? 'not-allowed' : 'pointer', transition: 'background 0.15s' }}>
            {generateMutation.isPending
              ? <><Loader size={13} className="animate-spin" /> Generating…</>
              : <><Zap size={13} /> Generate Report</>}
          </button>
        </div>
      </motion.div>

      {/* Generate success banner */}
      <AnimatePresence>
        {generateMutation.isSuccess && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: 10, padding: '12px 16px', fontSize: 13, color: '#15803D', fontWeight: 500 }}>
            <CheckCircle size={15} color="#22C55E" />
            Report generation triggered — the AI workflow is running. Results will appear below shortly.
          </motion.div>
        )}
      </AnimatePresence>

      {/* Filters */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        {/* Search */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'white', border: '1px solid #E5E7EB', borderRadius: 8, padding: '8px 14px', flex: '1 1 240px', maxWidth: 360 }}>
          <Search size={13} color="#9CA3AF" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search reports…"
            style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: 13, width: '100%', color: '#111827' }} />
        </div>
        {/* Type filter */}
        {['all', ...Object.keys(TYPE_CONFIG)].map(t => {
          const cfg = TYPE_CONFIG[t];
          const active = typeFilter === t;
          return (
            <button key={t} onClick={() => setTypeFilter(t)}
              style={{ padding: '7px 14px', borderRadius: 8, border: `1.5px solid ${active ? (cfg?.border || '#111827') : '#E5E7EB'}`, background: active ? (cfg?.bg || '#111827') : 'white', color: active ? (cfg?.text || 'white') : '#6B7280', fontSize: 12.5, fontWeight: active ? 700 : 400, cursor: 'pointer', textTransform: 'capitalize', transition: 'all 0.15s', whiteSpace: 'nowrap' }}>
              {t === 'all' ? 'All Reports' : (cfg?.label || t)}
            </button>
          );
        })}
      </motion.div>

      {/* Grid */}
      {isLoading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{ height: 220, background: '#F9FAFB', borderRadius: 14, animation: 'pulse 1.5s infinite' }} />
          ))}
        </div>
      ) : isError ? (
        <div style={{ padding: '40px 24px', textAlign: 'center', color: '#EF4444', fontSize: 14 }}>
          <AlertCircle size={32} color="#FCA5A5" style={{ marginBottom: 12 }} />
          <div>Failed to load reports. Check your backend connection.</div>
        </div>
      ) : filtered.length === 0 ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 24px', color: '#9CA3AF' }}>
          <FileText size={48} color="#E5E7EB" style={{ marginBottom: 16 }} />
          <div style={{ fontSize: 16, fontWeight: 700, color: '#374151', marginBottom: 8 }}>
            {search || typeFilter !== 'all' ? 'No reports match your filters' : 'No reports yet'}
          </div>
          <p style={{ fontSize: 13, maxWidth: 360, textAlign: 'center', lineHeight: 1.6 }}>
            {search || typeFilter !== 'all'
              ? 'Try adjusting your search or filter.'
              : 'Click "Generate Report" to trigger the AI workflow and create your first report.'}
          </p>
          {!search && typeFilter === 'all' && (
            <button onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}
              style={{ marginTop: 20, display: 'flex', alignItems: 'center', gap: 7, padding: '10px 20px', border: 'none', borderRadius: 9, fontSize: 13.5, fontWeight: 700, background: '#111827', color: 'white', cursor: 'pointer' }}>
              <Zap size={14} /> Generate First Report
            </button>
          )}
        </motion.div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {filtered.map((report, i) => (
            <ReportCard key={report.id || i} report={report} index={i} onPreview={setPreviewId} />
          ))}
        </div>
      )}

      {/* Preview modal */}
      <AnimatePresence>
        {previewId && <ReportModal reportId={previewId} onClose={() => setPreviewId(null)} />}
      </AnimatePresence>
    </div>
  );
}
