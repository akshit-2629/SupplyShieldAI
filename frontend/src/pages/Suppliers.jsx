import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, Star, Shield, TrendingUp, Users, ChevronUp, ChevronDown, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { scoreColor } from '../lib/utils';

const countryFlags = { TW: '🇹🇼', KR: '🇰🇷', DE: '🇩🇪', JP: '🇯🇵', US: '🇺🇸', SG: '🇸🇬', IN: '🇮🇳', FR: '🇫🇷', CN: '🇨🇳', NL: '🇳🇱' };

function ScoreBar({ value, color }) {
  return (
    <div style={{ height: 4, background: '#F3F4F6', borderRadius: 2, overflow: 'hidden', width: 60 }}>
      <motion.div initial={{ width: 0 }} animate={{ width: `${value || 0}%` }} transition={{ duration: 0.7, delay: 0.2 }}
        style={{ height: '100%', background: color || scoreColor(value), borderRadius: 2 }} />
    </div>
  );
}

function riskScoreColor(score) {
  if (score >= 80) return { bg: '#FEE2E2', color: '#DC2626' };
  if (score >= 60) return { bg: '#FEF3C7', color: '#D97706' };
  return { bg: '#D1FAE5', color: '#059669' };
}

function SupplierModal({ supplier, onClose }) {
  const rc = riskScoreColor(supplier.risk_score || 0);
  return (
    <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.div initial={{ opacity: 0, y: 20, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 20, scale: 0.96 }}
        onClick={e => e.stopPropagation()}
        style={{ width: 580, background: 'white', borderRadius: 14, boxShadow: '0 20px 60px rgba(0,0,0,0.12)', overflow: 'hidden', maxHeight: '90vh', overflowY: 'auto' }}
      >
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #F3F4F6', display: 'flex', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 48, height: 48, background: '#EFF6FF', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22 }}>
              {countryFlags[supplier.country_code] || '🏭'}
            </div>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: '#111827' }}>{supplier.name}</h2>
              <div style={{ fontSize: 12, color: '#9CA3AF' }}>{supplier.country_code} · {supplier.tier} · Rank #{supplier.rank || '—'}</div>
            </div>
          </div>
          <button onClick={onClose} style={{ background: '#F3F4F6', border: 'none', borderRadius: 8, width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
            <X size={16} color="#6B7280" />
          </button>
        </div>
        <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            {[
              { label: 'Health Score',   value: (supplier.health_score || 0).toFixed(1),   color: scoreColor(supplier.health_score) },
              { label: 'Reliability',    value: (supplier.reliability_score || 0).toFixed(1), color: scoreColor(supplier.reliability_score) },
              { label: 'Risk Score',     value: (supplier.risk_score || 0).toFixed(1),      color: rc.color },
            ].map(m => (
              <div key={m.label} style={{ background: '#FAFAFA', border: '1px solid #F3F4F6', borderRadius: 8, padding: 12, textAlign: 'center' }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: m.color }}>{m.value}</div>
                <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2 }}>{m.label}</div>
              </div>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {[
              { label: 'Tier',         value: supplier.tier || '—' },
              { label: 'Trend',        value: supplier.trend || '—' },
              { label: 'Rank',         value: `#${supplier.rank || '—'}` },
              { label: 'Revenue Exp.', value: supplier.revenue_exposure_pct ? `${supplier.revenue_exposure_pct.toFixed(1)}%` : '—' },
            ].map(i => (
              <div key={i.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#FAFAFA', borderRadius: 7, fontSize: 13 }}>
                <span style={{ color: '#9CA3AF' }}>{i.label}</span>
                <span style={{ fontWeight: 600, color: '#111827' }}>{i.value}</span>
              </div>
            ))}
          </div>
          {supplier.formula_breakdown && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#374151', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Score Breakdown</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {Object.entries(supplier.formula_breakdown).map(([key, val]) => (
                  <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#6B7280' }}>
                    <span>{key}</span><span style={{ fontWeight: 600, color: '#111827' }}>{typeof val === 'number' ? val.toFixed(2) : val}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function Suppliers() {
  const [search, setSearch] = useState('');
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [sortKey, setSortKey] = useState('health_score');
  const [sortDir, setSortDir] = useState('desc');

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['suppliers-list'],
    queryFn:  () => api.get('/suppliers/'),
  });

  const { data: fleet } = useQuery({
    queryKey: ['suppliers-fleet'],
    queryFn:  () => api.get('/suppliers/fleet'),
  });

  const suppliers = Array.isArray(data) ? data : Array.isArray(data?.suppliers) ? data.suppliers : [];

  const filtered = suppliers
    .filter(s => {
      const q = search.toLowerCase();
      return (s.name || '').toLowerCase().includes(q) || (s.country_code || '').toLowerCase().includes(q) || (s.tier || '').toLowerCase().includes(q);
    })
    .sort((a, b) => sortDir === 'desc' ? (b[sortKey] || 0) - (a[sortKey] || 0) : (a[sortKey] || 0) - (b[sortKey] || 0));

  function toggleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setSortDir('desc'); }
  }

  const SortIcon = ({ k }) => sortKey === k
    ? (sortDir === 'desc' ? <ChevronDown size={12} /> : <ChevronUp size={12} />)
    : null;

  const atRiskCount = suppliers.filter(s => (s.health_score || 0) < 70).length;
  const tier1Count  = suppliers.filter(s => (s.tier || '').includes('1')).length;
  const avgReliability = suppliers.length > 0
    ? Math.round(suppliers.reduce((a, s) => a + (s.reliability_score || 0), 0) / suppliers.length)
    : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1300 }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Supplier Management</h1>
          <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Monitor performance, reliability, and risk across your supplier portfolio</p>
        </div>
        <button onClick={() => refetch()} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </motion.div>

      {/* Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {[
          { label: 'Total Suppliers',  value: isLoading ? '…' : suppliers.length,      icon: Users,      color: '#2563EB', bg: '#EFF6FF' },
          { label: 'Tier 1 Strategic', value: isLoading ? '…' : tier1Count,             icon: Star,       color: '#7C3AED', bg: '#EDE9FE' },
          { label: 'At-Risk Suppliers',value: isLoading ? '…' : atRiskCount,            icon: Shield,     color: '#DC2626', bg: '#FEE2E2' },
          { label: 'Avg. Reliability', value: isLoading ? '…' : `${avgReliability}%`,   icon: TrendingUp, color: '#059669', bg: '#D1FAE5' },
        ].map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
            className="card" style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 12 }}
          >
            <div style={{ width: 36, height: 36, background: s.bg, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <s.icon size={18} color={s.color} />
            </div>
            <div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#111827' }}>{s.value}</div>
              <div style={{ fontSize: 11, color: '#9CA3AF' }}>{s.label}</div>
            </div>
          </motion.div>
        ))}
      </div>

      {isError && (
        <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, padding: '12px 16px', fontSize: 13, color: '#991B1B' }}>
          Failed to load supplier data. Make sure the backend is running and has executed an orchestrator trigger.
        </div>
      )}

      {/* Table */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid #F3F4F6', display: 'flex', gap: 12, alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#F5F5F5', border: '1px solid #E5E7EB', borderRadius: 8, padding: '7px 12px', flex: 1, maxWidth: 300 }}>
            <Search size={14} color="#9CA3AF" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search suppliers..." style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: 13, width: '100%' }} />
          </div>
          <span style={{ fontSize: 12, color: '#9CA3AF' }}>{isLoading ? '…' : `${filtered.length} suppliers`}</span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #F3F4F6', background: '#FAFAFA' }}>
                {['Supplier', 'Country', 'Tier', 'Health', 'Reliability', 'Risk Score', 'Trend', 'Status', ''].map(h => (
                  <th key={h} onClick={() => ['Health', 'Reliability', 'Risk Score'].includes(h) && toggleSort(h === 'Health' ? 'health_score' : h === 'Reliability' ? 'reliability_score' : 'risk_score')}
                    style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap', cursor: ['Health', 'Reliability', 'Risk Score'].includes(h) ? 'pointer' : 'default', userSelect: 'none' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      {h} {['Health', 'Reliability', 'Risk Score'].includes(h) && <SortIcon k={h === 'Health' ? 'health_score' : h === 'Reliability' ? 'reliability_score' : 'risk_score'} />}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array.from({ length: 6 }).map((_, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #F9FAFB' }}>
                      {Array.from({ length: 9 }).map((__, j) => (
                        <td key={j} style={{ padding: '14px' }}>
                          <div style={{ height: 12, background: '#F3F4F6', borderRadius: 4, width: j === 0 ? 120 : 60, animation: 'pulse 1.5s infinite' }} />
                        </td>
                      ))}
                    </tr>
                  ))
                : filtered.map((s, i) => {
                    const rc = riskScoreColor(s.risk_score || 0);
                    const isAtRisk = (s.health_score || 0) < 70;
                    return (
                      <motion.tr key={s.supplier_id || i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.04 }}
                        style={{ borderBottom: '1px solid #F9FAFB', cursor: 'pointer', transition: 'background 0.1s' }}
                        onMouseEnter={e => e.currentTarget.style.background = '#FAFAFA'}
                        onMouseLeave={e => e.currentTarget.style.background = 'white'}
                        onClick={() => setSelectedSupplier(s)}
                      >
                        <td style={{ padding: '12px 14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div style={{ fontSize: 18 }}>{countryFlags[s.country_code] || '🏭'}</div>
                            <span style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>{s.name || s.supplier_id}</span>
                          </div>
                        </td>
                        <td style={{ padding: '12px 14px', fontSize: 12.5, color: '#6B7280' }}>{s.country_code || '—'}</td>
                        <td style={{ padding: '12px 14px' }}>
                          <span style={{ background: (s.tier || '').includes('1') ? '#EDE9FE' : (s.tier || '').includes('2') ? '#EFF6FF' : '#F3F4F6', color: (s.tier || '').includes('1') ? '#5B21B6' : (s.tier || '').includes('2') ? '#1E40AF' : '#374151', fontSize: 11, fontWeight: 700, padding: '2px 7px', borderRadius: 6 }}>{s.tier || 'T?'}</span>
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <ScoreBar value={s.health_score} color={scoreColor(s.health_score)} />
                            <span style={{ fontSize: 12, fontWeight: 600, color: scoreColor(s.health_score) }}>{(s.health_score || 0).toFixed(0)}</span>
                          </div>
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <ScoreBar value={s.reliability_score} color={scoreColor(s.reliability_score)} />
                            <span style={{ fontSize: 12, fontWeight: 600, color: scoreColor(s.reliability_score) }}>{(s.reliability_score || 0).toFixed(0)}</span>
                          </div>
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <span style={{ background: rc.bg, color: rc.color, fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 8 }}>{(s.risk_score || 0).toFixed(0)}</span>
                        </td>
                        <td style={{ padding: '12px 14px', fontSize: 12, color: s.trend === 'IMPROVING' ? '#059669' : s.trend === 'DECLINING' ? '#DC2626' : '#6B7280' }}>{s.trend || '—'}</td>
                        <td style={{ padding: '12px 14px' }}>
                          <span style={{ background: isAtRisk ? '#FEF3C7' : '#D1FAE5', color: isAtRisk ? '#92400E' : '#065F46', fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 10, textTransform: 'capitalize' }}>
                            {isAtRisk ? 'at-risk' : 'active'}
                          </span>
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <button style={{ background: '#EFF6FF', color: '#2563EB', border: 'none', borderRadius: 6, padding: '5px 10px', fontSize: 12, cursor: 'pointer', fontWeight: 500 }}>Profile</button>
                        </td>
                      </motion.tr>
                    );
                  })}
            </tbody>
          </table>
        </div>
      </motion.div>

      <AnimatePresence>
        {selectedSupplier && <SupplierModal supplier={selectedSupplier} onClose={() => setSelectedSupplier(null)} />}
      </AnimatePresence>
    </div>
  );
}
