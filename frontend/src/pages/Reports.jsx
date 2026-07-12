import { useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, Download, Search, Plus, CheckCircle, Loader, Eye, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { formatDate } from '../lib/utils';

const typeColors = {
  executive: { bg: '#EDE9FE', text: '#5B21B6', border: '#C4B5FD' },
  risk:      { bg: '#FEE2E2', text: '#991B1B', border: '#FCA5A5' },
  supplier:  { bg: '#DBEAFE', text: '#1E40AF', border: '#93C5FD' },
  inventory: { bg: '#D1FAE5', text: '#065F46', border: '#6EE7B7' },
};

export default function Reports() {
  const [search, setSearch] = useState('');
  const [generating, setGenerating] = useState(false);

  // Reports endpoint is Phase 17 — not yet implemented.
  // We pull workflow run summaries from the orchestrator as a proxy.
  const { data: runs, refetch } = useQuery({
    queryKey: ['reports-runs'],
    queryFn:  () => api.get('/orchestrator/runs?limit=10'),
    staleTime: 60_000,
  });

  const runList = Array.isArray(runs?.runs) ? runs.runs : [];

  const reports = runList.map(r => ({
    id:          r.execution_id,
    title:       `Workflow Run — ${r.trigger_type} (${r.execution_id.slice(0, 8)}…)`,
    type:        'executive',
    generatedAt: r.completed_at || r.started_at,
    status:      r.status === 'completed' ? 'ready' : r.status === 'running' ? 'generating' : r.status,
    pages:       r.agent_count || 0,
    size:        '—',
  }));

  const filtered = reports.filter(r => r.title.toLowerCase().includes(search.toLowerCase()));

  function handleGenerate() {
    setGenerating(true);
    setTimeout(() => { setGenerating(false); refetch(); }, 1200);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1100 }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Reports Center</h1>
          <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>AI-generated supply chain intelligence reports</p>
        </div>
        <button onClick={handleGenerate} disabled={generating}
          style={{ display: 'flex', alignItems: 'center', gap: 8, background: generating ? '#F3F4F6' : '#111827', color: generating ? '#9CA3AF' : 'white', border: 'none', borderRadius: 8, padding: '10px 16px', fontSize: 13, fontWeight: 600, cursor: generating ? 'not-allowed' : 'pointer', transition: 'all 0.2s' }}>
          {generating ? <><Loader size={14} className="animate-spin-slow" /> Generating...</> : <><Plus size={14} /> Generate Report</>}
        </button>
      </motion.div>

      {/* Search */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'white', border: '1px solid #E5E7EB', borderRadius: 8, padding: '8px 14px', maxWidth: 400 }}>
          <Search size={14} color="#9CA3AF" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search reports..." style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: 13, width: '100%' }} />
        </div>
      </motion.div>

      {/* Reports Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 14 }}>
        {filtered.map((report, i) => {
          const tc = typeColors[report.type];
          return (
            <motion.div key={report.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }}
              className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}
              onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
            >
              {/* Icon + type */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ width: 40, height: 40, background: tc.bg, border: `1px solid ${tc.border}`, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <FileText size={18} color={tc.text} />
                </div>
                <span style={{ background: tc.bg, color: tc.text, border: `1px solid ${tc.border}`, fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 8, textTransform: 'capitalize' }}>{report.type}</span>
              </div>

              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 4, lineHeight: 1.3 }}>{report.title}</div>
                <div style={{ fontSize: 12, color: '#9CA3AF' }}>Generated {formatDate(report.generatedAt)}</div>
              </div>

              {/* Status */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                {report.status === 'ready' ? (
                  <><CheckCircle size={13} color="#059669" /><span style={{ color: '#059669', fontWeight: 500 }}>Ready</span></>
                ) : report.status === 'generating' ? (
                  <><Loader size={13} color="#D97706" className="animate-spin-slow" /><span style={{ color: '#D97706', fontWeight: 500 }}>Generating...</span></>
                ) : null}
                {report.pages > 0 && <span style={{ color: '#9CA3AF' }}>· {report.pages} pages · {report.size}</span>}
              </div>

              {/* Actions */}
              {report.status === 'ready' && (
                <div style={{ display: 'flex', gap: 8 }}>
                  <button style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 7, padding: '7px 10px', fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>
                    <Eye size={13} /> Preview
                  </button>
                  <button style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5, background: '#111827', color: 'white', border: 'none', borderRadius: 7, padding: '7px 10px', fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>
                    <Download size={13} /> Export
                  </button>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
