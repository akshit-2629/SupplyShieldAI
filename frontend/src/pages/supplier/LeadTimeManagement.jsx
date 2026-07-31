import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Clock, TrendingUp, Package, Truck, Box, Save, CheckCircle2, Info } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import PageHeader from '../../components/supplier/shared/PageHeader';
import { ProgressBar } from '../../components/supplier/shared/ProgressRing';
import { getLeadTimes, getLeadTimeHistory, updateLeadTime } from '../../services/supplierApi';

// Empty chart used when no history exists yet
const EMPTY_TREND = [
  { month: 'Jan', actual: 0, target: 0 },
  { month: 'Feb', actual: 0, target: 0 },
  { month: 'Mar', actual: 0, target: 0 },
  { month: 'Apr', actual: 0, target: 0 },
  { month: 'May', actual: 0, target: 0 },
  { month: 'Jun', actual: 0, target: 0 },
];

function TimeInput({ label, icon: Icon, value, onChange, unit = 'days', description, color = '#2563EB' }) {
  return (
    <div className="card" style={{ padding: '18px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <div style={{ width: 34, height: 34, borderRadius: 9, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Icon size={16} color={color} />
        </div>
        <div>
          <div style={{ fontSize: 13.5, fontWeight: 700, color: '#111827' }}>{label}</div>
          {description && <div style={{ fontSize: 11, color: '#9CA3AF' }}>{description}</div>}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <input
          type="number" min={0} value={value} onChange={(e) => onChange(Number(e.target.value))}
          style={{ width: 80, border: '1px solid #E5E7EB', borderRadius: 8, padding: '9px 12px', fontSize: 15, fontWeight: 700, textAlign: 'center', outline: 'none' }}
          onFocus={(e) => e.target.style.borderColor = color}
          onBlur={(e) => e.target.style.borderColor = '#E5E7EB'}
        />
        <span style={{ fontSize: 13, color: '#6B7280', fontWeight: 500 }}>{unit}</span>
        <div style={{ flex: 1, marginLeft: 8 }}>
          <ProgressBar value={Math.min(100, (value / 30) * 100)} color={color} height="5px" />
        </div>
      </div>
    </div>
  );
}

function SummaryBadge({ label, value, unit, color }) {
  return (
    <div style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 12, padding: '16px 20px', textAlign: 'center' }}>
      <div style={{ fontSize: 26, fontWeight: 800, color }}>{value}<span style={{ fontSize: 14, fontWeight: 500, color: '#9CA3AF', marginLeft: 4 }}>{unit}</span></div>
      <div style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>{label}</div>
    </div>
  );
}

export default function LeadTimeManagement() {
  const [saving, setSaving]   = useState(false);
  const [saved, setSaved]     = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [trendData, setTrendData]     = useState(EMPTY_TREND);
  const [times, setTimes] = useState({
    manufacturingDays: 7,
    packagingDays: 2,
    shippingDays: 5,
    averageDelay: 1,
    expectedDelivery: 15,
    notes: '',
  });

  useEffect(() => {
    // Load latest saved lead times to pre-populate form
    getLeadTimes()
      .then((data) => {
        if (Array.isArray(data) && data.length) {
          const latest = data[0];
          setTimes((prev) => ({
            ...prev,
            manufacturingDays: latest.manufacturing_days ?? prev.manufacturingDays,
            packagingDays:     latest.packaging_days     ?? prev.packagingDays,
            shippingDays:      latest.shipping_days      ?? prev.shippingDays,
            averageDelay:      latest.average_delay_days ?? prev.averageDelay,
            expectedDelivery:  latest.expected_delivery_days ?? prev.expectedDelivery,
            notes:             latest.notes ?? prev.notes,
          }));
        }
      })
      .catch(() => {/* form stays at defaults */});

    // Load trend history for chart
    getLeadTimeHistory()
      .then((history) => {
        if (Array.isArray(history) && history.length) {
          const sorted = [...history]
            .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
            .slice(-6)
            .map((r) => ({
              month:  new Date(r.created_at).toLocaleDateString('en', { month: 'short' }),
              actual: r.actual_days ?? 0,
              target: r.target_days ?? 0,
            }));
          setTrendData(sorted.length ? sorted : EMPTY_TREND);
        }
        setLoadingData(false);
      })
      .catch(() => setLoadingData(false));
  }, []);

  const set = (k) => (v) => setTimes((p) => ({ ...p, [k]: v }));
  const total = times.manufacturingDays + times.packagingDays + times.shippingDays;

  async function handleSave() {
    setSaving(true);
    try {
      const payload = {
        manufacturing_days: Number(times.manufacturingDays) || 0,
        packaging_days: Number(times.packagingDays) || 0,
        shipping_days: Number(times.shippingDays) || 0,
        average_delay_days: Number(times.averageDelay) || 0,
        expected_delivery_days: Number(times.expectedDelivery) || 0,
        total_lead_time_days: total,
        notes: times.notes || '',
      };
      await updateLeadTime(payload);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      getLeadTimeHistory().then((history) => {
        if (Array.isArray(history) && history.length) {
          const sorted = [...history]
            .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
            .slice(-6)
            .map((r) => ({
              month: new Date(r.created_at).toLocaleDateString('en', { month: 'short' }),
              actual: r.actual_days ?? 0,
              target: r.target_days ?? 0,
            }));
          setTrendData(sorted.length ? sorted : EMPTY_TREND);
        }
      }).catch(() => {});
    } catch (err) {
      console.error('Save lead time error:', err);
      alert(err.message || 'Failed to save lead times');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Lead Time Management"
        description="Define and track your manufacturing, packaging, and shipping lead times"
        actions={
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {saved && (
              <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
                style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#10B981', fontWeight: 600 }}>
                <CheckCircle2 size={15} /> Saved
              </motion.div>
            )}
            <button onClick={handleSave} disabled={saving}
              style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '9px 20px', border: 'none', borderRadius: 9, fontSize: 13.5, fontWeight: 700, background: saving ? '#9CA3AF' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', cursor: saving ? 'not-allowed' : 'pointer', boxShadow: '0 2px 10px rgba(16,185,129,0.3)' }}>
              <Save size={15} />{saving ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        }
      />

      {/* Summary row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, marginBottom: 24 }}>
        <SummaryBadge label="Total Lead Time" value={total} unit="days" color="#2563EB" />
        <SummaryBadge label="Avg Delay" value={times.averageDelay} unit="days" color="#F59E0B" />
        <SummaryBadge label="Expected Delivery" value={times.expectedDelivery} unit="days" color="#10B981" />
        <SummaryBadge label="Manufacturing" value={times.manufacturingDays} unit="days" color="#7C3AED" />
      </div>

      {/* Lead time breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <TimeInput label="Manufacturing Lead Time" icon={Package} value={times.manufacturingDays} onChange={set('manufacturingDays')} description="Time from order to production complete" color="#7C3AED" />
          <TimeInput label="Packaging Time" icon={Box} value={times.packagingDays} onChange={set('packagingDays')} description="Time to pack and prepare for dispatch" color="#F59E0B" />
          <TimeInput label="Shipping Time" icon={Truck} value={times.shippingDays} onChange={set('shippingDays')} description="Transit time from dispatch to delivery" color="#2563EB" />
          <TimeInput label="Average Delay" icon={Clock} value={times.averageDelay} onChange={set('averageDelay')} description="Historical average delay buffer" color="#EF4444" />
          <TimeInput label="Expected Delivery (Total)" icon={TrendingUp} value={times.expectedDelivery} onChange={set('expectedDelivery')} description="Customer-facing delivery estimate" color="#10B981" />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Visual breakdown */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 16 }}>Lead Time Breakdown</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { label: 'Manufacturing', value: times.manufacturingDays, max: total || 1, color: '#7C3AED' },
                { label: 'Packaging', value: times.packagingDays, max: total || 1, color: '#F59E0B' },
                { label: 'Shipping', value: times.shippingDays, max: total || 1, color: '#2563EB' },
              ].map(({ label, value, max, color }) => (
                <div key={label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontSize: 13, color: '#374151', fontWeight: 500 }}>{label}</span>
                    <span style={{ fontSize: 13, fontWeight: 700, color }}>{value}d ({Math.round((value / max) * 100)}%)</span>
                  </div>
                  <ProgressBar value={(value / max) * 100} color={color} height="8px" />
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: '12px 16px', background: '#F9FAFB', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Info size={14} color="#6B7280" />
              <span style={{ fontSize: 12, color: '#6B7280' }}>Total lead time: <strong style={{ color: '#111827' }}>{total} days</strong> + {times.averageDelay}d delay buffer = <strong style={{ color: '#10B981' }}>{total + times.averageDelay} days</strong></span>
            </div>
          </div>

          {/* Historical chart */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 4 }}>Historical Lead Time</h3>
            <p style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 16 }}>Actual vs Target · {loadingData ? 'Loading…' : `${trendData.length} records`}</p>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="actual" stroke="#2563EB" strokeWidth={2} dot={false} name="Actual (days)" />
                <Line type="monotone" dataKey="target" stroke="#10B981" strokeWidth={2} strokeDasharray="4 2" dot={false} name="Target (days)" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Notes */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: 8 }}>Notes</label>
            <textarea value={times.notes} onChange={(e) => set('notes')(e.target.value)} rows={4}
              placeholder="Any seasonal variations, regional exceptions, or notes about your lead times..."
              style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '9px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box', resize: 'vertical' }}
              onFocus={(e) => e.target.style.borderColor = '#10B981'} onBlur={(e) => e.target.style.borderColor = '#E5E7EB'} />
          </div>
        </div>
      </div>
    </div>
  );
}
