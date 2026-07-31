import { motion } from 'framer-motion';
import { Package, AlertTriangle, TrendingDown, Clock, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { api } from '../lib/api';

function StatusDot({ risk }) {
  const c = risk === 'CRITICAL' ? '#DC2626' : risk === 'HIGH' ? '#D97706' : risk === 'MEDIUM' ? '#D97706' : '#059669';
  return <div style={{ width: 8, height: 8, borderRadius: '50%', background: c, flexShrink: 0 }} />;
}

function statusLabel(risk) {
  if (risk === 'CRITICAL') return 'critical';
  if (risk === 'HIGH')     return 'warning';
  if (risk === 'SAFE')     return 'healthy';
  return 'ok';
}

export default function Inventory() {
  const { data: fleet,  isLoading: fleetLoading,  refetch: refetchFleet  } = useQuery({ queryKey: ['inventory-fleet'],  queryFn: () => api.get('/inventory/fleet') });
  const { data: items,  isLoading: itemsLoading,  refetch: refetchItems  } = useQuery({ queryKey: ['inventory-list'],   queryFn: () => api.get('/inventory/') });
  const { data: alerts, isLoading: alertsLoading                          } = useQuery({ queryKey: ['inventory-alerts'], queryFn: () => api.get('/inventory/alerts') });

  const isLoading = fleetLoading || itemsLoading;

  function refetchAll() { refetchFleet(); refetchItems(); }

  const components = Array.isArray(items) ? items : Array.isArray(items?.components) ? items.components : [];
  const alertItems = Array.isArray(alerts) ? alerts : Array.isArray(alerts?.alerts) ? alerts.alerts : [];

  const criticalCount = alertItems.filter(i => i.stockout_risk === 'CRITICAL').length;
  const highCount     = alertItems.filter(i => i.stockout_risk === 'HIGH').length;

  const healthScore = fleet?.fleet_inventory_health_score ?? fleet?.health_score ?? null;
  const revenueAtRisk = fleet?.total_revenue_lost_usd ?? fleet?.revenue_at_risk ?? 0;

  // Build depletion trend from component data
  const depletionData = components.slice(0, 5).map(c => ({
    name: (c.component_name || c.component_id || '?').slice(0, 12),
    days: Math.round(c.days_remaining || 0),
    risk: c.stockout_risk || 'SAFE',
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1300 }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Inventory Impact Dashboard</h1>
          <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Real-time inventory health and disruption impact assessment</p>
        </div>
        <button onClick={refetchAll} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </motion.div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {[
          { label: 'Inventory Health',   value: isLoading ? '…' : (healthScore != null ? `${healthScore.toFixed(0)}%` : '—'),                  sub: `${criticalCount} critical items`,       color: '#D97706', bg: '#FEF3C7', icon: Package },
          { label: 'Critical Items',     value: isLoading ? '…' : criticalCount,                                                                 sub: 'Stockout risk < 7 days',               color: '#DC2626', bg: '#FEE2E2', icon: AlertTriangle },
          { label: 'High-Risk Items',    value: isLoading ? '…' : highCount,                                                                     sub: 'Approaching threshold',                color: '#D97706', bg: '#FEF9C3', icon: Clock },
          { label: 'Revenue at Risk',    value: isLoading ? '…' : `$${(revenueAtRisk / 1_000_000).toFixed(1)}M`,                                sub: 'Est. impact from stockouts',           color: '#991B1B', bg: '#FEE2E2', icon: TrendingDown },
        ].map((k, i) => (
          <motion.div key={k.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
            className="card" style={{ padding: 16 }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
              <div style={{ width: 36, height: 36, background: k.bg, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <k.icon size={18} color={k.color} />
              </div>
            </div>
            <div style={{ fontSize: 24, fontWeight: 800, color: '#111827', marginBottom: 2 }}>{k.value}</div>
            <div style={{ fontSize: 12, color: '#9CA3AF' }}>{k.sub}</div>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 4 }}>Days of Supply by Component</div>
          <div style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 16 }}>Remaining stock days per component</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={depletionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} formatter={v => [`${v} days`, 'Days Remaining']} />
              <Bar dataKey="days" fill="#2563EB" radius={[4, 4, 0, 0]} name="Days Remaining" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 4 }}>Stockout Probability</div>
          <div style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 16 }}>Probability distribution across components</div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={components.slice(0, 8).map(c => ({
              name: (c.component_name || c.component_id || '?').slice(0, 10),
              prob: Math.round((c.stockout_probability || 0) * 100),
            }))}>
              <defs>
                <linearGradient id="probGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#DC2626" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#DC2626" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip contentStyle={{ border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} formatter={v => [`${v}%`, 'Stockout Probability']} />
              <Area type="monotone" dataKey="prob" stroke="#DC2626" strokeWidth={2} fill="url(#probGrad)" name="Probability %" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Component Table */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }} className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid #F3F4F6', fontSize: 14, fontWeight: 700, color: '#111827' }}>Critical Component Status</div>
        <table style={{ width: '100%' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #F3F4F6', background: '#FAFAFA' }}>
              {['Component', 'Current Stock', 'Days Remaining', 'Stockout Risk', 'Status', 'Revenue at Risk'].map(h => (
                <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #F9FAFB' }}>
                    {Array.from({ length: 6 }).map((__, j) => (
                      <td key={j} style={{ padding: '14px' }}>
                        <div style={{ height: 12, background: '#F3F4F6', borderRadius: 4, width: j === 0 ? 150 : 80 }} />
                      </td>
                    ))}
                  </tr>
                ))
              : components.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ padding: '32px 14px', textAlign: 'center', color: '#9CA3AF', fontSize: 13 }}>
                      No components have been added yet. Go to Business Management to add components.
                    </td>
                  </tr>
                ) : components.map((item, i) => (
                  <motion.tr key={item.component_id || i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 + i * 0.05 }}
                    style={{ borderBottom: '1px solid #F9FAFB' }}
                  >
                    <td style={{ padding: '12px 14px', fontSize: 13, fontWeight: 500, color: '#111827' }}>
                      {item.component_name || item.component_id}
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 13, color: '#374151' }}>
                      {(item.current_stock ?? item.item?.current_stock ?? 0).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: 60, height: 5, background: '#F3F4F6', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${Math.min(100, ((item.days_remaining || 0) / 60) * 100)}%`, height: '100%', background: item.stockout_risk === 'CRITICAL' ? '#DC2626' : item.stockout_risk === 'HIGH' ? '#D97706' : '#059669', borderRadius: 3 }} />
                        </div>
                        <span style={{ fontSize: 12, fontWeight: 600, color: item.stockout_risk === 'CRITICAL' ? '#DC2626' : item.stockout_risk === 'HIGH' ? '#D97706' : '#059669' }}>{(item.days_remaining || 0).toFixed(0)}d</span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12, color: '#374151' }}>{item.stockout_risk || '—'}</td>
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <StatusDot risk={item.stockout_risk} />
                        <span style={{ fontSize: 12, fontWeight: 600, color: item.stockout_risk === 'CRITICAL' ? '#DC2626' : item.stockout_risk === 'HIGH' ? '#D97706' : '#059669', textTransform: 'capitalize' }}>
                          {statusLabel(item.stockout_risk)}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12, color: '#374151' }}>
                      {item.revenue_lost_usd ? `$${(item.revenue_lost_usd / 1_000_000).toFixed(2)}M` : '—'}
                    </td>
                  </motion.tr>
                ))}
          </tbody>
        </table>
      </motion.div>
    </div>
  );
}
