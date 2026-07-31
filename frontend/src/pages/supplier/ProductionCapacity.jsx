import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Factory, Users, Settings, Calendar, Zap, Save, CheckCircle2, AlertTriangle } from 'lucide-react';
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts';
import PageHeader from '../../components/supplier/shared/PageHeader';
import { ProgressBar } from '../../components/supplier/shared/ProgressRing';
import StatusBadge from '../../components/supplier/shared/StatusBadge';
import { updateProductionCapacity, getProductionCapacity } from '../../services/supplierApi';

const FACTORY_STATUSES = ['Fully Operational', 'Partial Capacity', 'Maintenance', 'Shutdown'];
const SHIFT_OPTIONS = ['Single Shift (8h)', 'Double Shift (16h)', 'Triple Shift (24h)', 'Custom'];

function MetricSlider({ label, value, onChange, color = '#10B981', unit = '%', max = 100 }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>{label}</label>
        <span style={{ fontSize: 13, fontWeight: 800, color }}>
          {value}{unit}
        </span>
      </div>
      <input type="range" min={0} max={max} value={value} onChange={(e) => onChange(Number(e.target.value))}
        style={{ width: '100%', accentColor: color, cursor: 'pointer', height: 4 }} />
      <ProgressBar value={(value / max) * 100} color={color} height="6px" />
    </div>
  );
}

function StatBox({ label, value, unit, color = '#111827', bg = '#F9FAFB' }) {
  return (
    <div style={{ background: bg, borderRadius: 10, padding: '14px 18px', textAlign: 'center', border: '1px solid #E5E7EB' }}>
      <div style={{ fontSize: 22, fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 10, color: '#9CA3AF', fontWeight: 600, marginTop: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
      {unit && <div style={{ fontSize: 11, color: '#6B7280', marginTop: 2 }}>{unit}</div>}
    </div>
  );
}

export default function ProductionCapacity() {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [capacity, setCapacity] = useState({
    factoryStatus: 'Fully Operational',
    currentCapacity: 75,
    machineUtilization: 68,
    workforceAvailability: 82,
    shiftPattern: 'Double Shift (16h)',
    maxDailyOutput: 500,
    currentOutputRate: 375,
    plannedMaintenance: '',
    downtimeHours: 0,
    notes: '',
  });

  useEffect(() => {
    getProductionCapacity().then((res) => {
      if (res) {
        const statusReverseMap = {
          OPERATIONAL: 'Fully Operational',
          PARTIAL: 'Partial Capacity',
          MAINTENANCE: 'Maintenance',
          OFFLINE: 'Shutdown',
        };
        setCapacity((prev) => ({
          ...prev,
          factoryStatus: statusReverseMap[res.factory_status] || prev.factoryStatus,
          currentCapacity: res.utilization_pct ?? prev.currentCapacity,
          maxDailyOutput: res.maximum_capacity_units ?? prev.maxDailyOutput,
          currentOutputRate: res.current_output_units ?? prev.currentOutputRate,
          workforceAvailability: res.workforce_count ?? prev.workforceAvailability,
          downtimeHours: res.planned_downtime_days ? res.planned_downtime_days * 24 : prev.downtimeHours,
          notes: res.notes ?? prev.notes,
        }));
      }
    }).catch(() => {});
  }, []);

  const set = (k) => (v) => setCapacity((p) => ({ ...p, [k]: v }));

  async function handleSave() {
    setSaving(true);
    try {
      const statusMap = {
        'Fully Operational': 'OPERATIONAL',
        'Partial Capacity': 'PARTIAL',
        'Maintenance': 'MAINTENANCE',
        'Shutdown': 'OFFLINE',
      };
      const payload = {
        factory_status: statusMap[capacity.factoryStatus] || 'OPERATIONAL',
        utilization_pct: Number(capacity.currentCapacity) || 0,
        maximum_capacity_units: Number(capacity.maxDailyOutput) || 0,
        current_output_units: Number(capacity.currentOutputRate) || 0,
        production_rate_per_day: Number(capacity.currentOutputRate) || 0,
        workforce_count: Number(capacity.workforceAvailability) || 0,
        shifts_per_day: capacity.shiftPattern?.includes('Triple') ? 3 : capacity.shiftPattern?.includes('Double') ? 2 : 1,
        planned_downtime_days: Math.ceil((Number(capacity.downtimeHours) || 0) / 24),
        notes: capacity.notes || '',
      };
      await updateProductionCapacity(payload);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Save production capacity error:', err);
      alert(err.message || 'Failed to save production capacity');
    } finally {
      setSaving(false);
    }
  }

  const utilizationColor = capacity.machineUtilization >= 80 ? '#10B981' : capacity.machineUtilization >= 50 ? '#F59E0B' : '#EF4444';
  const efficiencyPct = capacity.maxDailyOutput > 0 ? Math.round((capacity.currentOutputRate / capacity.maxDailyOutput) * 100) : 0;

  return (
    <div>
      <PageHeader
        title="Production Capacity"
        description="Update your current production status, utilization metrics, and shift information"
        actions={
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {saved && (
              <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}
                style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#10B981', fontWeight: 600 }}>
                <CheckCircle2 size={15} /> Saved successfully
              </motion.div>
            )}
            <button onClick={handleSave} disabled={saving}
              style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '9px 20px', border: 'none', borderRadius: 9, fontSize: 13.5, fontWeight: 700, background: saving ? '#9CA3AF' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', cursor: saving ? 'not-allowed' : 'pointer', boxShadow: '0 2px 10px rgba(16,185,129,0.3)' }}>
              <Save size={15} /> {saving ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        }
      />

      {/* Summary Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 12, marginBottom: 24 }}>
        <StatBox label="Capacity Used" value={`${capacity.currentCapacity}%`} color={capacity.currentCapacity > 85 ? '#EF4444' : '#10B981'} bg="#ECFDF5" />
        <StatBox label="Machine Utilization" value={`${capacity.machineUtilization}%`} color={utilizationColor} />
        <StatBox label="Workforce" value={`${capacity.workforceAvailability}%`} color="#2563EB" bg="#EFF6FF" />
        <StatBox label="Efficiency" value={`${efficiencyPct}%`} color="#F59E0B" bg="#FFFBEB" />
        <StatBox label="Max Output" value={capacity.maxDailyOutput} unit="units/day" />
        <StatBox label="Current Rate" value={capacity.currentOutputRate} unit="units/day" color="#10B981" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Main form */}
        <div>
          {/* Factory Status */}
          <div className="card" style={{ padding: '20px 24px', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <div style={{ width: 32, height: 32, background: '#ECFDF5', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Factory size={16} color="#10B981" /></div>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>Factory Status</h3>
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
              {FACTORY_STATUSES.map((s) => (
                <button key={s} onClick={() => set('factoryStatus')(s)}
                  style={{ padding: '7px 14px', borderRadius: 8, border: `1.5px solid ${capacity.factoryStatus === s ? '#10B981' : '#E5E7EB'}`, background: capacity.factoryStatus === s ? '#ECFDF5' : 'white', color: capacity.factoryStatus === s ? '#059669' : '#6B7280', fontSize: 13, fontWeight: capacity.factoryStatus === s ? 700 : 400, cursor: 'pointer', transition: 'all 0.15s' }}>
                  {s}
                </button>
              ))}
            </div>
            {capacity.factoryStatus !== 'Fully Operational' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 8, fontSize: 13, color: '#92400E' }}>
                <AlertTriangle size={14} color="#F59E0B" />
                Factory is not at full capacity. Please provide details below.
              </div>
            )}
          </div>

          {/* Utilization Sliders */}
          <div className="card" style={{ padding: '20px 24px', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <div style={{ width: 32, height: 32, background: '#EFF6FF', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Zap size={16} color="#2563EB" /></div>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>Utilization Metrics</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
              <MetricSlider label="Current Production Capacity" value={capacity.currentCapacity} onChange={set('currentCapacity')} color="#10B981" />
              <MetricSlider label="Machine Utilization Rate" value={capacity.machineUtilization} onChange={set('machineUtilization')} color="#2563EB" />
              <MetricSlider label="Workforce Availability" value={capacity.workforceAvailability} onChange={set('workforceAvailability')} color="#F59E0B" />
              <MetricSlider label="Downtime Hours (this week)" value={capacity.downtimeHours} onChange={set('downtimeHours')} color="#EF4444" unit="h" max={168} />
            </div>
          </div>

          {/* Output */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 16 }}>Output & Shifts</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', display: 'block', marginBottom: 6 }}>Max Daily Output (units)</label>
                <input type="number" value={capacity.maxDailyOutput} onChange={(e) => set('maxDailyOutput')(Number(e.target.value))}
                  style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '9px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box' }}
                  onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; }} />
              </div>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', display: 'block', marginBottom: 6 }}>Current Output Rate (units)</label>
                <input type="number" value={capacity.currentOutputRate} onChange={(e) => set('currentOutputRate')(Number(e.target.value))}
                  style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '9px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box' }}
                  onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; }} />
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', display: 'block', marginBottom: 8 }}>Working Shifts</label>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {SHIFT_OPTIONS.map((s) => (
                  <button key={s} onClick={() => set('shiftPattern')(s)}
                    style={{ padding: '6px 14px', borderRadius: 7, border: `1.5px solid ${capacity.shiftPattern === s ? '#10B981' : '#E5E7EB'}`, background: capacity.shiftPattern === s ? '#ECFDF5' : 'white', color: capacity.shiftPattern === s ? '#059669' : '#6B7280', fontSize: 12.5, fontWeight: capacity.shiftPattern === s ? 700 : 400, cursor: 'pointer', transition: 'all 0.15s' }}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', display: 'block', marginBottom: 6 }}>Notes / Additional Information</label>
              <textarea value={capacity.notes} onChange={(e) => set('notes')(e.target.value)} rows={3} placeholder="Any additional context about current production status..."
                style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '9px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box', resize: 'vertical' }}
                onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; }} />
            </div>
          </div>
        </div>

        {/* Right panel: visual gauges */}
        <div>
          <div className="card" style={{ padding: '20px 24px', marginBottom: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 8 }}>Capacity Gauge</h3>
            <div style={{ height: 180 }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart cx="50%" cy="50%" innerRadius="40%" outerRadius="85%"
                  data={[
                    { name: 'Workforce', value: capacity.workforceAvailability, fill: '#F59E0B' },
                    { name: 'Machines', value: capacity.machineUtilization, fill: '#2563EB' },
                    { name: 'Capacity', value: capacity.currentCapacity, fill: '#10B981' },
                  ]}
                  startAngle={180} endAngle={0}>
                  <RadialBar dataKey="value" background={{ fill: '#F3F4F6' }} cornerRadius={4} />
                  <Tooltip formatter={(v) => `${v}%`} />
                </RadialBarChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
              {[{ label: 'Capacity', value: capacity.currentCapacity, color: '#10B981' }, { label: 'Machines', value: capacity.machineUtilization, color: '#2563EB' }, { label: 'Workforce', value: capacity.workforceAvailability, color: '#F59E0B' }].map((item) => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 3, background: item.color, flexShrink: 0 }} />
                  <span style={{ fontSize: 12, color: '#6B7280', flex: 1 }}>{item.label}</span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#111827' }}>{item.value}%</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ padding: '20px 24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <div style={{ width: 28, height: 28, background: '#FFFBEB', borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Calendar size={14} color="#F59E0B" /></div>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>Maintenance</h3>
            </div>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', display: 'block', marginBottom: 6 }}>Next Planned Maintenance</label>
              <input type="date" value={capacity.plannedMaintenance} onChange={(e) => set('plannedMaintenance')(e.target.value)}
                style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '9px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box' }}
                onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; }} />
            </div>
            <div style={{ marginTop: 14, padding: '12px', background: '#F9FAFB', borderRadius: 8 }}>
              <div style={{ fontSize: 12, color: '#6B7280', marginBottom: 4 }}>Current Status</div>
              <StatusBadge status={capacity.factoryStatus === 'Fully Operational' ? 'active' : capacity.factoryStatus === 'Maintenance' ? 'pending' : 'high'} label={capacity.factoryStatus} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
