import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Star, Shield, Activity, Heart, Brain, Info, Lock, TrendingUp, TrendingDown, Minus, ChevronDown } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import PageHeader from '../../components/supplier/shared/PageHeader';
import ScoreRing from '../../components/supplier/shared/ScoreRing';
import { SkeletonCard } from '../../components/supplier/shared/SkeletonCard';
import { getPerformanceMetrics, getMetricsHistory } from '../../services/supplierApi';

const METRICS = [
  {
    key: 'reliability',
    label: 'Reliability Score',
    icon: Shield,
    color: '#10B981',
    bg: '#ECFDF5',
    description: 'Measures your on-time delivery rate, order fulfillment accuracy, and consistency over time.',
    factors: ['On-time delivery rate', 'Order accuracy', 'Return rate', 'Communication responsiveness'],
  },
  {
    key: 'performance',
    label: 'Performance Score',
    icon: Star,
    color: '#2563EB',
    bg: '#EFF6FF',
    description: 'Evaluates production output efficiency, capacity utilization, and throughput against benchmarks.',
    factors: ['Production efficiency', 'Capacity utilization', 'Throughput rate', 'Quality output'],
  },
  {
    key: 'risk',
    label: 'Risk Score',
    icon: Activity,
    color: '#EF4444',
    bg: '#FEF2F2',
    description: 'AI-assessed risk level based on geopolitical factors, financial health, and operational indicators.',
    factors: ['Geopolitical exposure', 'Financial stability', 'Incident history', 'Supply chain concentration'],
    inverted: true,
  },
  {
    key: 'health',
    label: 'Health Score',
    icon: Heart,
    color: '#F59E0B',
    bg: '#FFFBEB',
    description: 'Overall operational health combining all dimensions of supplier performance.',
    factors: ['Overall reliability', 'Risk-adjusted performance', 'Compliance status', 'Relationship quality'],
  },
  {
    key: 'confidence',
    label: 'AI Confidence',
    icon: Brain,
    color: '#7C3AED',
    bg: '#F5F3FF',
    description: 'Indicates how much data the AI model has to generate accurate scores for your account.',
    factors: ['Data completeness', 'Historical depth', 'Update frequency', 'Verification status'],
  },
];


function MetricCard({ metric, scores, loading }) {
  const [expanded, setExpanded] = useState(false);
  const score = scores?.[metric.key] ?? scores?.[`${metric.key}_score`] ?? (metric.key === 'performance' ? scores?.quality_score : 0) ?? 0;
  const prev = scores?.[`${metric.key}_prev`] ?? 0;
  const delta = score - prev;
  const Icon = metric.icon;

  return (
    <div className="card" style={{ padding: '20px 24px', overflow: 'hidden' }}>
      {/* Read-only banner */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, background: '#F3F4F6', borderRadius: 6, padding: '4px 10px', marginBottom: 16, width: 'fit-content' }}>
        <Lock size={11} color="#9CA3AF" />
        <span style={{ fontSize: 10.5, color: '#9CA3AF', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>AI Generated · Read-only</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 16 }}>
        <ScoreRing score={score} color={metric.color} size={96} loading={loading} />
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <div style={{ width: 28, height: 28, borderRadius: 7, background: metric.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Icon size={14} color={metric.color} />
            </div>
            <h3 style={{ fontSize: 14.5, fontWeight: 700, color: '#111827' }}>{metric.label}</h3>
          </div>
          <p style={{ fontSize: 12.5, color: '#6B7280', lineHeight: 1.6, marginBottom: 10 }}>{metric.description}</p>
          {delta !== 0 && (
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12, fontWeight: 600, color: delta > 0 ? '#10B981' : '#EF4444', background: delta > 0 ? '#ECFDF5' : '#FEF2F2', borderRadius: 6, padding: '3px 8px' }}>
              {delta > 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {Math.abs(delta)} pts vs last month
            </div>
          )}
        </div>
      </div>

      <button onClick={() => setExpanded(!expanded)}
        style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#6B7280', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500, padding: 0 }}>
        <Info size={13} /> What factors affect this score?
        <ChevronDown size={13} style={{ transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
      </button>

      {expanded && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
          style={{ marginTop: 12, padding: '12px 14px', background: '#F9FAFB', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>Contributing Factors</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {metric.factors.map((f) => (
              <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: '#374151' }}>
                <div style={{ width: 5, height: 5, borderRadius: '50%', background: metric.color, flexShrink: 0 }} />
                {f}
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default function PerformanceMetrics() {
  const [loading, setLoading] = useState(true);
  const [scores, setScores] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    Promise.all([getPerformanceMetrics(), getMetricsHistory()])
      .then(([s, h]) => { setScores(s); if (Array.isArray(h) && h.length) setHistory(h); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="AI Performance Metrics"
        description="AI-generated scores based on your operational data — updated automatically"
      />

      {/* Read-only notice */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 10, padding: '12px 16px', marginBottom: 24, fontSize: 13, color: '#92400E' }}>
        <Lock size={15} color="#F59E0B" />
        <div>
          <strong>These scores are read-only.</strong> They are generated by the SupplyShield AI engine based on your operational data, incident history, and market signals. Keep your profile and data up to date to improve your scores.
        </div>
      </motion.div>

      {/* Score grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16, marginBottom: 24 }}>
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} rows={4} height={200} />)
        ) : (
          METRICS.map((m) => <MetricCard key={m.key} metric={m} scores={scores} loading={loading} />)
        )}
      </div>

      {/* Historical trend */}
      <div className="card" style={{ padding: '20px 24px' }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 4 }}>Score History</h3>
        <p style={{ fontSize: 12, color: '#9CA3AF', marginBottom: 20 }}>6-month trend across all metrics · Updated automatically by AI engine</p>
        {history.length === 0 ? (
          <div style={{ height: 180, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#9CA3AF', fontSize: 13 }}>
            <TrendingUp size={32} color="#E5E7EB" style={{ marginBottom: 10 }} />
            No history data yet. Complete your setup and keep data up to date to build your score history.
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} />
                {METRICS.filter((m) => m.key !== 'confidence').map((m) => (
                  <Line key={m.key} type="monotone" dataKey={m.key} stroke={m.color} strokeWidth={2} dot={false} name={m.label} />
                ))}
              </LineChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 12, justifyContent: 'center' }}>
              {METRICS.filter((m) => m.key !== 'confidence').map((m) => (
                <div key={m.key} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                  <div style={{ width: 12, height: 3, background: m.color, borderRadius: 2 }} />
                  <span style={{ color: '#6B7280' }}>{m.label}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

    </div>
  );
}
