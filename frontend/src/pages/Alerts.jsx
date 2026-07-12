import { motion } from 'framer-motion';
import { Bell, CheckCheck, X, AlertTriangle, Cpu, Package, Building2, RefreshCw } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { severityColor, timeAgo } from '../lib/utils';
import { useState } from 'react';

const categoryIcon  = { disruption: AlertTriangle, supplier: Building2, inventory: Package, ai: Cpu, system: Bell };
const categoryColor = { disruption: '#DC2626', supplier: '#D97706', inventory: '#2563EB', ai: '#7C3AED', system: '#6B7280' };

/**
 * Alerts page — shows the latest HIGH/CRITICAL events from /risk/assessments + agent alerts.
 * We composite alerts from:
 *   - /risk/assessments (HIGH/CRITICAL) → disruption category
 *   - /inventory/alerts (CRITICAL/HIGH stockout)  → inventory category
 *   - /suppliers/alerts  → supplier category
 */
export default function Alerts() {
  const [filter, setFilter] = useState('all');
  const [dismissed, setDismissed] = useState(new Set());

  const { data: riskData,      refetch: refetchRisk      } = useQuery({ queryKey: ['alerts-risk'],      queryFn: () => api.get('/risk/assessments') });
  const { data: invData,       refetch: refetchInv        } = useQuery({ queryKey: ['alerts-inventory'], queryFn: () => api.get('/inventory/alerts') });
  const { data: supplierData,  refetch: refetchSupplier   } = useQuery({ queryKey: ['alerts-suppliers'], queryFn: () => api.get('/suppliers/alerts') });

  function refetchAll() { refetchRisk(); refetchInv(); refetchSupplier(); }

  // Build a unified alerts list from the three sources
  const rawAlerts = [
    // Risk alerts (HIGH/CRITICAL only)
    ...(Array.isArray(riskData) ? riskData : riskData?.assessments || [])
      .filter(r => ['HIGH', 'CRITICAL'].includes(r.risk_level))
      .map(r => ({
        id:        `risk-${r.assessment_id}`,
        title:     r.title || 'Risk Alert',
        message:   `Risk score ${(r.risk_score || 0).toFixed(0)}/100. Trajectory: ${r.trajectory || 'N/A'}. Countries: ${(r.countries || []).join(', ') || 'N/A'}.`,
        severity:  r.risk_level?.toLowerCase(),
        timestamp: r.assessed_at,
        category:  'disruption',
        read:      false,
      })),
    // Inventory alerts
    ...(Array.isArray(invData) ? invData : invData?.alerts || [])
      .map(i => ({
        id:        `inv-${i.component_id}`,
        title:     `Stockout Alert: ${i.component_name || i.component_id}`,
        message:   `${i.days_remaining?.toFixed(0) || '?'} days remaining. Risk: ${i.stockout_risk}. Revenue at risk: $${((i.revenue_lost_usd || 0) / 1_000_000).toFixed(2)}M.`,
        severity:  i.stockout_risk === 'CRITICAL' ? 'critical' : 'high',
        timestamp: i.evaluated_at,
        category:  'inventory',
        read:      false,
      })),
    // Supplier alerts
    ...(Array.isArray(supplierData) ? supplierData : supplierData?.alerts || [])
      .map(s => ({
        id:        `sup-${s.supplier_id}`,
        title:     `Supplier Alert: ${s.name || s.supplier_id}`,
        message:   `Health score ${(s.health_score || 0).toFixed(0)}/100. Trend: ${s.trend || 'N/A'}. Tier: ${s.tier || 'N/A'}.`,
        severity:  (s.health_score || 100) < 50 ? 'critical' : 'high',
        timestamp: s.evaluated_at,
        category:  'supplier',
        read:      false,
      })),
  ].sort((a, b) => {
    const order = { critical: 0, high: 1, medium: 2, low: 3 };
    return (order[a.severity] ?? 4) - (order[b.severity] ?? 4);
  });

  const alerts = rawAlerts.filter(a => !dismissed.has(a.id));
  const filtered = alerts.filter(a => filter === 'all' || a.severity === filter || (filter === 'unread' && !a.read));
  const unreadCount = alerts.filter(a => !a.read).length;

  function dismiss(id) { setDismissed(prev => new Set([...prev, id])); }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 900 }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
            Alert Center
            {unreadCount > 0 && <span style={{ background: '#DC2626', color: 'white', fontSize: 12, fontWeight: 700, padding: '1px 8px', borderRadius: 10 }}>{unreadCount}</span>}
          </h1>
          <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Priority alerts from your supply chain intelligence system</p>
        </div>
        <button onClick={refetchAll} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </motion.div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {[
          { key: 'all',      label: 'All Alerts', count: alerts.length },
          { key: 'critical', label: 'Critical',   count: alerts.filter(a => a.severity === 'critical').length },
          { key: 'high',     label: 'High',       count: alerts.filter(a => a.severity === 'high').length },
        ].map(f => (
          <button key={f.key} onClick={() => setFilter(f.key)}
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: filter === f.key ? '#EFF6FF' : 'white', color: filter === f.key ? '#2563EB' : '#6B7280', border: `1px solid ${filter === f.key ? '#BFDBFE' : '#E5E7EB'}`, borderRadius: 8, padding: '7px 14px', fontSize: 13, fontWeight: filter === f.key ? 600 : 400, cursor: 'pointer', transition: 'all 0.15s' }}>
            {f.label}
            {f.count > 0 && <span style={{ background: filter === f.key ? '#DBEAFE' : '#F3F4F6', color: filter === f.key ? '#1E40AF' : '#6B7280', fontSize: 11, fontWeight: 700, padding: '1px 7px', borderRadius: 8 }}>{f.count}</span>}
          </button>
        ))}
      </div>

      {/* Alert List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {filtered.length === 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card" style={{ padding: 48, textAlign: 'center', color: '#9CA3AF' }}>
            <Bell size={36} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
            <div style={{ fontSize: 14, fontWeight: 600 }}>No alerts found</div>
            <div style={{ fontSize: 13, marginTop: 4 }}>Run the AI Workflow to generate live alerts.</div>
          </motion.div>
        )}
        {filtered.map((alert, i) => {
          const sc   = severityColor(alert.severity);
          const Icon = categoryIcon[alert.category] || Bell;
          return (
            <motion.div key={alert.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
              className="card" style={{ padding: '14px 16px', background: alert.read ? 'white' : '#FAFBFF', borderLeft: `3px solid ${sc.dot}` }}
            >
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                {!alert.read && <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#2563EB', marginTop: 4, flexShrink: 0 }} />}
                <div style={{ width: 32, height: 32, background: sc.bg, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Icon size={15} color={sc.dot} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: '#111827' }}>{alert.title}</div>
                    <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                      <span style={{ background: sc.bg, color: sc.text, fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 8, textTransform: 'uppercase' }}>{alert.severity}</span>
                      <span style={{ fontSize: 11, color: '#9CA3AF', whiteSpace: 'nowrap' }}>{timeAgo(alert.timestamp)}</span>
                    </div>
                  </div>
                  <p style={{ fontSize: 12.5, color: '#6B7280', lineHeight: 1.5, marginBottom: 8 }}>{alert.message}</p>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={() => dismiss(alert.id)} style={{ background: '#F3F4F6', color: '#6B7280', border: 'none', borderRadius: 6, padding: '4px 10px', fontSize: 12, cursor: 'pointer', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 4 }}>
                      <X size={11} /> Dismiss
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
