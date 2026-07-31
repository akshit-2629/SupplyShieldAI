import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Factory, Package, Truck, AlertTriangle, TrendingUp,
  CheckCircle2, Clock, Bell, Zap, ArrowRight, BarChart2,
  ShieldCheck, Star, Activity
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useSupplierAuth } from '../../context/SupplierAuthContext';
import StatCard from '../../components/supplier/shared/StatCard';
import ScoreRing from '../../components/supplier/shared/ScoreRing';
import StatusBadge from '../../components/supplier/shared/StatusBadge';
import { SkeletonCard } from '../../components/supplier/shared/SkeletonCard';
import { getSupplierDashboard } from '../../services/supplierApi';
import { useNavigate } from 'react-router-dom';

// ── Chart data builders ───────────────────────────────────────────────────
function buildProductionChart(history) {
  if (!history?.length) return [];
  const sorted = [...history].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  return sorted.slice(-6).map((r) => ({
    month: new Date(r.created_at).toLocaleDateString('en', { month: 'short' }),
    capacity: r.maximum_capacity_units || 0,
    output:   r.current_output_units   || 0,
  }));
}

function buildInventoryChart(items) {
  if (!items?.length) return [];
  const groups = {};
  items.forEach((item) => {
    const cat = item.category || 'Other';
    groups[cat] = (groups[cat] || 0) + (item.quantity_on_hand || 0);
  });
  return Object.entries(groups)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name, value]) => ({ name, value }));
}

const EMPTY_PRODUCTION = [
  { month: 'Jan', capacity: 0, output: 0 },
  { month: 'Feb', capacity: 0, output: 0 },
  { month: 'Mar', capacity: 0, output: 0 },
  { month: 'Apr', capacity: 0, output: 0 },
  { month: 'May', capacity: 0, output: 0 },
  { month: 'Jun', capacity: 0, output: 0 },
];

const EMPTY_INVENTORY = [
  { name: 'No Data', value: 0 },
];

const QUICK_ACTIONS = [
  { label: 'Update Production', icon: Factory, color: '#10B981', bg: '#ECFDF5', to: '/supplier/production' },
  { label: 'Report Incident', icon: AlertTriangle, color: '#EF4444', bg: '#FEF2F2', to: '/supplier/incidents' },
  { label: 'Track Shipment', icon: Truck, color: '#2563EB', bg: '#EFF6FF', to: '/supplier/shipments' },
  { label: 'Update Inventory', icon: Package, color: '#F59E0B', bg: '#FFFBEB', to: '/supplier/inventory' },
];

function ScoreCard({ label, score, color, loading }) {
  return (
    <div className="card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
      {loading ? (
        <><div className="skeleton" style={{ width: 90, height: 90, borderRadius: '50%' }} />
          <div className="skeleton" style={{ width: 80, height: 12, borderRadius: 6 }} /></>
      ) : (
        <>
          <ScoreRing score={score} label={label} color={color} size={90} />
          <div style={{ fontSize: 11, color: '#6B7280', textAlign: 'center' }}>AI Generated Score</div>
        </>
      )}
    </div>
  );
}

export default function SupplierDashboard() {
  const { supplierUser } = useSupplierAuth();
  const [loading, setLoading]   = useState(true);
  const [dashData, setDashData] = useState(null);
  const [error, setError]       = useState(null);
  const navigate = useNavigate();

  const companyName = supplierUser?.user_metadata?.companyName || 'Your Company';
  const contactName = supplierUser?.user_metadata?.contactName?.split(' ')[0] || 'there';

  useEffect(() => {
    getSupplierDashboard()
      .then((data) => { setDashData(data); setLoading(false); })
      .catch((err)  => { setError(err.message); setLoading(false); });
  }, []);

  // Derived chart data
  const productionData = dashData?.productionHistory?.length
    ? buildProductionChart(dashData.productionHistory)
    : EMPTY_PRODUCTION;
  const inventoryData = dashData?.inventoryItems?.length
    ? buildInventoryChart(dashData.inventoryItems)
    : EMPTY_INVENTORY;

  // Derived scores (fall back to 0 when no AI run has been done yet)
  const scores = dashData?.scores || {};

  const cardAnim = (i) => ({ initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { delay: i * 0.06, duration: 0.4 } });

  return (
    <div>
      {/* Welcome card */}
      <motion.div {...cardAnim(0)} style={{ background: 'linear-gradient(135deg, #10B981 0%, #059669 50%, #047857 100%)', borderRadius: 16, padding: '28px 32px', marginBottom: 24, position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', top: -40, right: -40, width: 180, height: 180, background: 'rgba(255,255,255,0.07)', borderRadius: '50%' }} />
        <div style={{ position: 'absolute', bottom: -30, right: 100, width: 120, height: 120, background: 'rgba(255,255,255,0.05)', borderRadius: '50%' }} />
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.7)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Welcome back</div>
            <h2 style={{ fontSize: 26, fontWeight: 800, color: 'white', marginBottom: 4 }}>Hello, {contactName} 👋</h2>
            <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.8)' }}>{companyName} · Supplier Portal</p>
          </div>
            <div style={{ display: 'flex', gap: 16 }}>
            <div style={{ background: 'rgba(255,255,255,0.15)', borderRadius: 12, padding: '12px 20px', textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 800, color: 'white' }}>{loading ? '—' : dashData?.openShipments ?? 0}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>Open Shipments</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.15)', borderRadius: 12, padding: '12px 20px', textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 800, color: 'white' }}>{loading ? '—' : dashData?.activeIncidents ?? 0}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>Active Incidents</div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Status Row */}
      <motion.div {...cardAnim(1)} style={{ display: 'flex', gap: 10, marginBottom: 24, flexWrap: 'wrap' }}>
        {[
          { label: 'Account Status',  value: 'Approved',                              icon: CheckCircle2, color: '#10B981' },
          { label: 'Inventory Items', value: loading ? '…' : (dashData?.inventoryItems?.length ?? 0), icon: Package,      color: '#2563EB' },
          { label: 'Unread Alerts',   value: loading ? '…' : (dashData?.unreadNotifications ?? 0),   icon: Bell,         color: '#EF4444' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'white', border: '1px solid #E5E7EB', borderRadius: 10, padding: '8px 16px', fontSize: 13 }}>
            <Icon size={15} color={color} />
            <span style={{ color: '#6B7280' }}>{label}:</span>
            <span style={{ fontWeight: 700, color: '#111827' }}>{value}</span>
          </div>
        ))}
      </motion.div>

      {/* KPI Grid */}
      <motion.div {...cardAnim(2)} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
        <StatCard label="Production Capacity" value={loading ? '—' : (dashData?.production?.current_output_units ?? '—')} icon={Factory}       iconColor="#10B981" iconBg="#ECFDF5" loading={loading} subtitle="Units / day" />
        <StatCard label="Inventory Items"     value={loading ? '—' : (dashData?.inventoryItems?.length ?? 0)}             icon={Package}       iconColor="#2563EB" iconBg="#EFF6FF" loading={loading} />
        <StatCard label="Open Shipments"      value={loading ? '—' : (dashData?.openShipments ?? 0)}                     icon={Truck}         iconColor="#F59E0B" iconBg="#FFFBEB" loading={loading} />
        <StatCard label="Active Incidents"    value={loading ? '—' : (dashData?.activeIncidents ?? 0)}                  icon={AlertTriangle} iconColor="#EF4444" iconBg="#FEF2F2" loading={loading} />
      </motion.div>

      {/* AI Scores row */}
      <motion.div {...cardAnim(3)} style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>AI Performance Scores</h3>
            <p style={{ fontSize: 12, color: '#6B7280' }}>Generated by SupplyShield AI · Read-only</p>
          </div>
          <button onClick={() => navigate('/supplier/metrics')} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#10B981', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}>
            View Details <ArrowRight size={13} />
          </button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 16 }}>
          <ScoreCard label="Reliability"  score={scores.reliability_score ?? 0} color="#10B981" loading={loading} />
          <ScoreCard label="Quality"      score={scores.quality_score      ?? 0} color="#2563EB" loading={loading} />
          <ScoreCard label="Risk Score"   score={scores.risk_score         ?? 0} color="auto"   loading={loading} />
          <ScoreCard label="Health Score" score={scores.health_score       ?? 0} color="#F59E0B" loading={loading} />
        </div>
      </motion.div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <motion.div {...cardAnim(4)} className="card" style={{ padding: '20px 24px' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 4 }}>Production Trend</div>
          <div style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 20 }}>Capacity vs Output · Last {productionData.length} updates</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={productionData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
              <defs>
                <linearGradient id="capGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} />
              <Area type="monotone" dataKey="capacity" stroke="#10B981" fill="url(#capGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="output" stroke="#2563EB" fill="transparent" strokeWidth={2} strokeDasharray="4 2" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div {...cardAnim(5)} className="card" style={{ padding: '20px 24px' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 4 }}>Inventory Overview</div>
          <div style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 20 }}>By category · {dashData?.inventoryItems?.length ?? 0} total items</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={inventoryData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="value" fill="#2563EB" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Quick Actions + Recent Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <motion.div {...cardAnim(6)} className="card" style={{ padding: '20px 24px' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 16 }}>Quick Actions</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {QUICK_ACTIONS.map(({ label, icon: Icon, color, bg, to }) => (
              <button key={label} onClick={() => navigate(to)}
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, padding: '16px 12px', border: '1px solid #E5E7EB', borderRadius: 10, background: 'white', cursor: 'pointer', transition: 'all 0.15s' }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = color; e.currentTarget.style.background = bg; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#E5E7EB'; e.currentTarget.style.background = 'white'; }}
              >
                <div style={{ width: 38, height: 38, borderRadius: 10, background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={18} color={color} />
                </div>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#374151', textAlign: 'center' }}>{label}</span>
              </button>
            ))}
          </div>
        </motion.div>

        <motion.div {...cardAnim(7)} className="card" style={{ padding: '20px 24px' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 16 }}>Recent Activity</div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px 0', gap: 10 }}>
            <div style={{ width: 48, height: 48, borderRadius: 14, background: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Activity size={22} color="#9CA3AF" />
            </div>
            <p style={{ fontSize: 13, color: '#9CA3AF', textAlign: 'center' }}>No recent activity yet.<br />Your actions will appear here.</p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
