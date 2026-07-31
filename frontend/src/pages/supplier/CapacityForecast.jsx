import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, Save, CheckCircle2, Info, TrendingUp, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import PageHeader from '../../components/supplier/shared/PageHeader';
import { submitForecast, getForecast } from '../../services/supplierApi';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const CURRENT_YEAR = new Date().getFullYear();

function buildForecast(year) {
  return MONTHS.map((month) => ({
    month,
    year,
    forecastedOutput: 0,
    maximumCapacity: 0,
    plannedDowntime: 0,
  }));
}

export default function CapacityForecast() {
  const [period, setPeriod] = useState('monthly');
  const [year, setYear] = useState(CURRENT_YEAR);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState(buildForecast(CURRENT_YEAR));
  const [editingRow, setEditingRow] = useState(null);

  // Load saved forecast from backend when year changes
  useEffect(() => {
    setLoading(true);
    getForecast(period, year)
      .then((data) => {
        if (Array.isArray(data) && data.length === 12) {
          // Map backend rows to our local shape
          setForecast(data.map((r) => ({
            month:             r.month || r.period_month,
            year:              r.year  || r.period_year || year,
            forecastedOutput:  r.forecasted_output  ?? r.forecastedOutput  ?? 0,
            maximumCapacity:   r.maximum_capacity   ?? r.maximumCapacity   ?? 0,
            plannedDowntime:   r.planned_downtime   ?? r.plannedDowntime   ?? 0,
          })));
        } else {
          // No data for this year — start fresh
          setForecast(buildForecast(year));
        }
      })
      .catch(() => setForecast(buildForecast(year)))
      .finally(() => setLoading(false));
  }, [year, period]);

  function updateRow(i, key, val) {
    setForecast((prev) => prev.map((r, ri) => ri === i ? { ...r, [key]: Number(val) } : r));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const monthMap = { Jan: 1, Feb: 2, Mar: 3, Apr: 4, May: 5, Jun: 6, Jul: 7, Aug: 8, Sep: 9, Oct: 10, Nov: 11, Dec: 12 };
      const entries = forecast.map((f) => ({
        forecast_month: monthMap[f.month] || 1,
        forecasted_output: Number(f.forecastedOutput) || 0,
        maximum_capacity: Number(f.maximumCapacity) || 0,
        planned_downtime_days: Number(f.plannedDowntime) || 0,
      }));
      await submitForecast({
        forecast_year: Number(year),
        period_type: period,
        entries,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      getForecast(period, year).then((data) => {
        if (Array.isArray(data) && data.length === 12) {
          setForecast(data.map((r) => ({
            month: r.month || r.period_month,
            year: r.year || r.period_year || year,
            forecastedOutput: r.forecasted_output ?? r.forecastedOutput ?? 0,
            maximumCapacity: r.maximum_capacity ?? r.maximumCapacity ?? 0,
            plannedDowntime: r.planned_downtime ?? r.plannedDowntime ?? 0,
          })));
        }
      }).catch(() => {});
    } catch (err) {
      console.error('Submit forecast error:', err);
      alert(err.message || 'Failed to submit forecast');
    } finally {
      setSaving(false);
    }
  }

  const quarterly = [
    { quarter: 'Q1', ...(['Jan', 'Feb', 'Mar'].reduce((a, m) => { const r = forecast.find((f) => f.month === m); return { forecastedOutput: a.forecastedOutput + r.forecastedOutput, maximumCapacity: a.maximumCapacity + r.maximumCapacity }; }, { forecastedOutput: 0, maximumCapacity: 0 })) },
    { quarter: 'Q2', ...(['Apr', 'May', 'Jun'].reduce((a, m) => { const r = forecast.find((f) => f.month === m); return { forecastedOutput: a.forecastedOutput + r.forecastedOutput, maximumCapacity: a.maximumCapacity + r.maximumCapacity }; }, { forecastedOutput: 0, maximumCapacity: 0 })) },
    { quarter: 'Q3', ...(['Jul', 'Aug', 'Sep'].reduce((a, m) => { const r = forecast.find((f) => f.month === m); return { forecastedOutput: a.forecastedOutput + r.forecastedOutput, maximumCapacity: a.maximumCapacity + r.maximumCapacity }; }, { forecastedOutput: 0, maximumCapacity: 0 })) },
    { quarter: 'Q4', ...(['Oct', 'Nov', 'Dec'].reduce((a, m) => { const r = forecast.find((f) => f.month === m); return { forecastedOutput: a.forecastedOutput + r.forecastedOutput, maximumCapacity: a.maximumCapacity + r.maximumCapacity }; }, { forecastedOutput: 0, maximumCapacity: 0 })) },
  ];

  const chartData = period === 'monthly' ? forecast.map((r) => ({ name: r.month, 'Forecast': r.forecastedOutput, 'Max Capacity': r.maximumCapacity, 'Downtime': r.plannedDowntime })) : quarterly.map((r) => ({ name: r.quarter, 'Forecast': r.forecastedOutput, 'Max Capacity': r.maximumCapacity }));

  const totalForecast = forecast.reduce((a, r) => a + r.forecastedOutput, 0);
  const totalCapacity = forecast.reduce((a, r) => a + r.maximumCapacity, 0);
  const utilization = totalCapacity > 0 ? Math.round((totalForecast / totalCapacity) * 100) : 0;

  const inputSt = { border: '1px solid #E5E7EB', borderRadius: 6, padding: '5px 8px', fontSize: 13, outline: 'none', width: '100%', textAlign: 'right', boxSizing: 'border-box' };

  return (
    <div>
      <PageHeader
        title="Capacity Forecast"
        description="Plan and submit your monthly or quarterly production capacity forecasts"
        actions={
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {loading && <Loader2 size={15} color="#9CA3AF" className="animate-spin" />}
            {saved && (
              <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
                style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#10B981', fontWeight: 600 }}>
                <CheckCircle2 size={15} /> Submitted
              </motion.div>
            )}
            <button onClick={handleSave} disabled={saving || loading}
              style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '9px 20px', border: 'none', borderRadius: 9, fontSize: 13.5, fontWeight: 700, background: saving ? '#9CA3AF' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', cursor: saving ? 'not-allowed' : 'pointer', boxShadow: '0 2px 10px rgba(16,185,129,0.3)' }}>
              <Save size={15} />{saving ? 'Submitting…' : 'Submit Forecast'}
            </button>
          </div>
        }
      />

      {/* Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: 6 }}>
          {['monthly', 'quarterly'].map((p) => (
            <button key={p} onClick={() => setPeriod(p)}
              style={{ padding: '7px 18px', borderRadius: 8, border: `1.5px solid ${period === p ? '#10B981' : '#E5E7EB'}`, background: period === p ? '#ECFDF5' : 'white', color: period === p ? '#059669' : '#6B7280', fontSize: 13, fontWeight: period === p ? 700 : 400, cursor: 'pointer', textTransform: 'capitalize', transition: 'all 0.15s' }}>
              {p}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={() => setYear((y) => y - 1)} style={{ padding: '6px 10px', border: '1px solid #E5E7EB', borderRadius: 7, background: 'white', cursor: 'pointer' }}><ChevronLeft size={14} /></button>
          <span style={{ fontSize: 14, fontWeight: 700, color: '#111827', minWidth: 50, textAlign: 'center' }}>{year}</span>
          <button onClick={() => setYear((y) => y + 1)} style={{ padding: '6px 10px', border: '1px solid #E5E7EB', borderRadius: 7, background: 'white', cursor: 'pointer' }}><ChevronRight size={14} /></button>
        </div>
      </div>

      {/* Summary KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12, marginBottom: 24 }}>
        {[
          { label: 'Total Forecast Output', value: totalForecast.toLocaleString(), unit: 'units', color: '#10B981' },
          { label: 'Total Max Capacity', value: totalCapacity.toLocaleString(), unit: 'units', color: '#2563EB' },
          { label: 'Utilization Rate', value: `${utilization}%`, unit: '', color: utilization > 80 ? '#EF4444' : utilization > 60 ? '#F59E0B' : '#10B981' },
          { label: 'Months Planned', value: forecast.filter((r) => r.forecastedOutput > 0).length, unit: `/ 12`, color: '#7C3AED' },
        ].map(({ label, value, unit, color }) => (
          <div key={label} className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: 22, fontWeight: 800, color }}>{value} <span style={{ fontSize: 13, fontWeight: 400, color: '#9CA3AF' }}>{unit}</span></div>
            <div style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="card" style={{ padding: '20px 24px', marginBottom: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 20 }}>Forecast vs Capacity — {year}</h3>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -12 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="Forecast" fill="#10B981" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Max Capacity" fill="#E5E7EB" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Editable forecast table */}
      {period === 'monthly' && (
        <div className="card" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>Monthly Forecast Editor</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: '#6B7280', background: '#F3F4F6', borderRadius: 6, padding: '3px 10px' }}>
              <Info size={12} /> Click cells to edit
            </div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#F9FAFB' }}>
                  {['Month', 'Forecasted Output (units)', 'Maximum Capacity (units)', 'Planned Downtime (days)'].map((h) => (
                    <th key={h} style={{ padding: '10px 14px', textAlign: h === 'Month' ? 'left' : 'right', fontSize: 11, fontWeight: 700, color: '#6B7280', letterSpacing: '0.04em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {forecast.map((row, i) => (
                  <tr key={row.month} style={{ borderTop: '1px solid #F3F4F6' }}
                    onMouseEnter={(e) => e.currentTarget.style.background = '#F9FAFB'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                    <td style={{ padding: '10px 14px', fontWeight: 600, color: '#374151' }}>{row.month}</td>
                    {['forecastedOutput', 'maximumCapacity', 'plannedDowntime'].map((key) => (
                      <td key={key} style={{ padding: '6px 14px', textAlign: 'right' }}>
                        <input type="number" min={0} value={row[key]} onChange={(e) => updateRow(i, key, e.target.value)}
                          style={inputSt}
                          onFocus={(e) => e.target.style.borderColor = '#10B981'}
                          onBlur={(e) => e.target.style.borderColor = '#E5E7EB'} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
