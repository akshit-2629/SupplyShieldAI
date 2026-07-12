import { motion } from 'framer-motion';
import { Stars, ArrowRight, RefreshCw, AlertCircle } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

const flagMap = { US: '🇺🇸', KR: '🇰🇷', TW: '🇹🇼', DE: '🇩🇪', JP: '🇯🇵', SG: '🇸🇬' };

function ScoreRadar({ supplier }) {
  const data = [
    { metric: 'TOPSIS',   value: Math.round((supplier.top_topsis_score || 0) * 100) },
    { metric: 'Cosine',   value: Math.round((supplier.top_cosine_sim || 0) * 100) },
    { metric: 'Score',    value: Math.round((supplier.top_recommendation_score || 0) * 100) },
  ];
  return (
    <ResponsiveContainer width="100%" height={160}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius={60}>
        <PolarGrid stroke="#F3F4F6" />
        <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10, fill: '#9CA3AF' }} />
        <Radar dataKey="value" stroke="#2563EB" fill="#2563EB" fillOpacity={0.12} strokeWidth={2} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

export default function Recommendations() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['recommendations-list'],
    queryFn:  () => api.get('/recommendations/'),
  });

  const { data: summary } = useQuery({
    queryKey: ['recommendations-summary'],
    queryFn:  () => api.get('/recommendations/summary'),
  });

  const recs = Array.isArray(data) ? data : Array.isArray(data?.recommendations) ? data.recommendations : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 1300 }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Supplier Recommendations</h1>
          <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>AI-ranked alternative suppliers via TOPSIS + MCDM + Cosine Similarity</p>
        </div>
        <button onClick={() => refetch()} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </motion.div>

      {/* Context banner */}
      {summary && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 10, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10 }}
        >
          <Stars size={16} color="#2563EB" />
          <span style={{ fontSize: 13, color: '#1E40AF' }}>
            AI Orchestrator identified <strong>{summary.at_risk_supplier_count || recs.length}</strong> at-risk supplier(s) and generated ranked alternatives.
            {summary.immediate_switch_count > 0 && <> <strong>{summary.immediate_switch_count}</strong> require immediate action.</>}
          </span>
        </motion.div>
      )}

      {isError && (
        <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#991B1B' }}>
          <AlertCircle size={16} />
          No recommendations yet. Run the AI Workflow from the Orchestration Center first.
        </div>
      )}

      {!isLoading && !isError && recs.length === 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card" style={{ padding: 48, textAlign: 'center', color: '#9CA3AF' }}>
          <Stars size={36} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
          <div style={{ fontSize: 14, fontWeight: 600 }}>No Recommendations Available</div>
          <div style={{ fontSize: 13, marginTop: 4 }}>Run the AI Orchestrator to generate supplier recommendations.</div>
        </motion.div>
      )}

      {/* Recommendation Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="card" style={{ padding: 20, height: 360, background: '#FAFAFA', animation: 'pulse 1.5s infinite' }} />
            ))
          : recs.map((rec, i) => (
              <motion.div key={rec.at_risk_supplier_id || i} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 + i * 0.1 }}
                className="card" style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}
              >
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 2 }}>At-Risk Supplier</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: '#DC2626' }}>{rec.at_risk_supplier_name || rec.at_risk_supplier_id}</div>
                    <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2 }}>Stockout: {rec.stockout_risk || '—'}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 11, color: '#9CA3AF', marginBottom: 2 }}>Revenue at Risk</div>
                    <div style={{ fontSize: 15, fontWeight: 800, color: '#DC2626' }}>
                      {rec.revenue_at_risk_usd ? `$${(rec.revenue_at_risk_usd / 1_000_000).toFixed(2)}M` : '—'}
                    </div>
                  </div>
                </div>

                <div style={{ height: 1, background: '#F3F4F6' }} />

                {/* Top Alternative */}
                <div>
                  <div style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 6 }}>Top Alternative Supplier</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ fontSize: 22 }}>{flagMap[rec.top_country_code] || '🏭'}</div>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>{rec.top_supplier_name || rec.top_supplier_id || '—'}</div>
                      <div style={{ fontSize: 11, color: '#9CA3AF' }}>{rec.top_tier || '—'} · {rec.top_country_code || '—'}</div>
                    </div>
                    <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                      <div style={{ fontSize: 22, fontWeight: 800, color: '#2563EB' }}>
                        {rec.top_recommendation_score ? (rec.top_recommendation_score * 100).toFixed(0) : '—'}
                      </div>
                      <div style={{ fontSize: 10, color: '#9CA3AF' }}>MCDM Score</div>
                    </div>
                  </div>
                </div>

                {/* Rank badge */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ background: i === 0 ? '#FEF9C3' : i === 1 ? '#F3F4F6' : '#FEF3C7', color: '#92400E', fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 10 }}>
                    {i === 0 ? '🥇 #1' : i === 1 ? '🥈 #2' : `#${i + 1}`} Recommendation
                  </span>
                  <span style={{ background: rec.procurement_action === 'IMMEDIATE_SWITCH' ? '#FEE2E2' : '#EFF6FF', color: rec.procurement_action === 'IMMEDIATE_SWITCH' ? '#DC2626' : '#2563EB', fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 8 }}>
                    {(rec.procurement_action || '—').replace(/_/g, ' ')}
                  </span>
                </div>

                {/* Score bars */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {[
                    { label: 'TOPSIS',  value: Math.round((rec.top_topsis_score || 0) * 100) },
                    { label: 'Cosine',  value: Math.round((rec.top_cosine_sim || 0) * 100) },
                    { label: 'Overall', value: Math.round((rec.top_recommendation_score || 0) * 100) },
                  ].map(m => (
                    <div key={m.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                      <span style={{ width: 55, color: '#6B7280' }}>{m.label}</span>
                      <div style={{ flex: 1, height: 5, background: '#F3F4F6', borderRadius: 3, overflow: 'hidden' }}>
                        <motion.div initial={{ width: 0 }} animate={{ width: `${m.value}%` }} transition={{ duration: 0.7, delay: 0.3 + i * 0.1 }}
                          style={{ height: '100%', background: '#2563EB', borderRadius: 3 }} />
                      </div>
                      <span style={{ width: 28, fontWeight: 600, color: '#374151', textAlign: 'right' }}>{m.value}</span>
                    </div>
                  ))}
                </div>

                {/* Explanation */}
                {rec.explanation && (
                  <div style={{ background: '#F9FAFB', border: '1px solid #F3F4F6', borderRadius: 8, padding: '10px 12px', fontSize: 12, color: '#6B7280', lineHeight: 1.6 }}>
                    {rec.explanation.slice(0, 140)}…
                  </div>
                )}

                {/* Action */}
                <button style={{ width: '100%', background: '#111827', color: 'white', border: 'none', borderRadius: 8, padding: '10px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, transition: 'background 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.background = '#374151'}
                  onMouseLeave={e => e.currentTarget.style.background = '#111827'}
                >
                  <ArrowRight size={14} /> Select {rec.top_supplier_name || 'Alternative'}
                </button>
              </motion.div>
            ))}
      </div>
    </div>
  );
}
