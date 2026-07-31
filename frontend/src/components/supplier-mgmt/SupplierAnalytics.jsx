/**
 * SupplierAnalytics.jsx — Aggregated analytics dashboard for the Supplier Management module.
 */

import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Users, Clock, CheckCircle2, XCircle, Pause, Send, TrendingUp, Shield, Star, RefreshCw } from 'lucide-react';
import { getSupplierAnalytics } from '../../services/supplierManagementApi';

const RISK_COLORS = {
  LOW:      '#10B981',
  MEDIUM:   '#F59E0B',
  HIGH:     '#F97316',
  CRITICAL: '#EF4444',
  UNKNOWN:  '#9CA3AF',
};

function KpiCard({ icon: Icon, label, value, sub, color = '#2563EB', bg = '#EFF6FF' }) {
  return (
    <div style={{
      background: 'white', border: '1px solid #E5E7EB', borderRadius: 12,
      padding: '18px 20px', display: 'flex', gap: 14, alignItems: 'center',
    }}>
      <div style={{
        width: 44, height: 44, borderRadius: 12, background: bg,
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>
        <Icon size={20} color={color} />
      </div>
      <div>
        <div style={{ fontSize: 22, fontWeight: 800, color: '#111827', lineHeight: 1.2 }}>{value}</div>
        <div style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', marginTop: 2 }}>{label}</div>
        {sub && <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2 }}>{sub}</div>}
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
      <p style={{ margin: 0, fontWeight: 700, color: '#111827' }}>{label || payload[0]?.name}</p>
      <p style={{ margin: '2px 0 0', color: '#6B7280' }}>Count: <strong style={{ color: '#111827' }}>{payload[0]?.value}</strong></p>
    </div>
  );
};

export default function SupplierAnalytics() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const res = await getSupplierAnalytics();
      setData(res);
    } catch (_) {}
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300, gap: 10 }}>
        <RefreshCw size={18} color="#2563EB" style={{ animation: 'spin 1s linear infinite' }} />
        <span style={{ fontSize: 14, color: '#6B7280' }}>Loading analytics…</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: 60, color: '#9CA3AF', fontSize: 14 }}>
        Failed to load analytics. <button onClick={load} style={{ color: '#2563EB', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 700 }}>Retry</button>
      </div>
    );
  }

  // Prepare chart data
  const statusData = [
    { name: 'Active',    value: data.active_suppliers,    color: '#10B981' },
    { name: 'Pending',   value: data.pending_approval,    color: '#F59E0B' },
    { name: 'Suspended', value: data.suspended_suppliers, color: '#6B7280' },
    { name: 'Rejected',  value: data.rejected_suppliers,  color: '#EF4444' },
  ].filter(d => d.value > 0);

  const riskData = Object.entries(data.risk_distribution || {})
    .filter(([, v]) => v > 0)
    .map(([k, v]) => ({ name: k, value: v, color: RISK_COLORS[k] }));

  const invitationData = [
    { name: 'Sent',      value: data.total_invitations },
    { name: 'Pending',   value: data.pending_invitations },
    { name: 'Accepted',  value: data.accepted_invitations },
    { name: 'Expired',   value: data.expired_invitations },
  ];

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Refresh */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button onClick={load} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 12px', borderRadius: 7, border: '1px solid #E5E7EB', background: 'white', color: '#6B7280', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {/* KPI Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14 }}>
        <KpiCard icon={Users}        label="Total Suppliers"   value={data.total_suppliers}      color="#2563EB" bg="#EFF6FF" />
        <KpiCard icon={CheckCircle2} label="Active"            value={data.active_suppliers}     color="#10B981" bg="#D1FAE5" />
        <KpiCard icon={Clock}        label="Pending Approval"  value={data.pending_approval}     color="#F59E0B" bg="#FEF3C7" />
        <KpiCard icon={Pause}        label="Suspended"         value={data.suspended_suppliers}  color="#6B7280" bg="#F3F4F6" />
        <KpiCard icon={XCircle}      label="Rejected"          value={data.rejected_suppliers}   color="#EF4444" bg="#FEE2E2" />
        <KpiCard icon={Star}         label="Critical Suppliers" value={data.critical_suppliers}  color="#F97316" bg="#FFEDD5" />
        <KpiCard icon={Send}         label="Invitations Sent"  value={data.total_invitations}    color="#7C3AED" bg="#F5F3FF" />
        <KpiCard icon={TrendingUp}   label="Acceptance Rate"
          value={`${data.acceptance_rate}%`}
          sub={`${data.accepted_invitations} of ${data.total_invitations} accepted`}
          color="#10B981" bg="#D1FAE5"
        />
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>

        {/* Status Distribution */}
        {statusData.length > 0 && (
          <div style={chartCard}>
            <h4 style={chartTitle}>Supplier Status</h4>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={statusData} cx="50%" cy="50%" innerRadius={50} outerRadius={75}
                  dataKey="value" paddingAngle={3}>
                  {statusData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', marginTop: 4 }}>
              {statusData.map(d => (
                <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: '#374151', fontWeight: 600 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: d.color }} />
                  {d.name} ({d.value})
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Risk Distribution */}
        {riskData.length > 0 && (
          <div style={chartCard}>
            <h4 style={chartTitle}>Risk Rating Distribution</h4>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={riskData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {riskData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Invitation Funnel */}
        <div style={chartCard}>
          <h4 style={chartTitle}>Invitation Funnel</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
            {invitationData.map(({ name, value }) => {
              const pct = data.total_invitations > 0 ? (value / data.total_invitations) * 100 : 0;
              const col = name === 'Sent' ? '#2563EB' : name === 'Accepted' ? '#10B981' : name === 'Pending' ? '#F59E0B' : '#9CA3AF';
              return (
                <div key={name}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 4 }}>
                    <span>{name}</span><span style={{ color: col }}>{value}</span>
                  </div>
                  <div style={{ height: 6, background: '#F3F4F6', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: col, borderRadius: 3, transition: 'width 0.6s ease' }} />
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ marginTop: 16, padding: '10px 14px', background: '#F0FDF4', borderRadius: 8, border: '1px solid #BBF7D0' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#065F46' }}>Acceptance Rate</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#10B981', marginTop: 2 }}>{data.acceptance_rate}%</div>
          </div>
        </div>
      </div>

      {/* Shield banner */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16,
        background: 'linear-gradient(135deg, #EFF6FF, #F5F3FF)',
        border: '1px solid #DBEAFE', borderRadius: 12, padding: '16px 20px',
      }}>
        <Shield size={22} color="#2563EB" />
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>
            {data.critical_suppliers} critical supplier{data.critical_suppliers !== 1 ? 's' : ''} in your network
          </div>
          <div style={{ fontSize: 12, color: '#6B7280', marginTop: 2 }}>
            Monitor these closely — any disruption has immediate production impact.
          </div>
        </div>
      </div>
    </div>
  );
}

const chartCard = {
  background: 'white', border: '1px solid #E5E7EB', borderRadius: 12, padding: '16px 18px',
};
const chartTitle = {
  fontSize: 12, fontWeight: 700, color: '#374151',
  textTransform: 'uppercase', letterSpacing: '0.04em', margin: '0 0 8px',
};
