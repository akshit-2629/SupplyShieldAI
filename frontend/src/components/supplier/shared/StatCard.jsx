import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

/**
 * StatCard — KPI card with icon, value, label, and optional trend indicator.
 * @param {string} label
 * @param {string|number} value
 * @param {React.ComponentType} icon
 * @param {string} iconColor - CSS color
 * @param {string} iconBg - CSS color for icon background
 * @param {number} [trend] - positive/negative percent, or undefined
 * @param {string} [trendLabel] - e.g. "vs last month"
 * @param {boolean} [loading]
 * @param {string} [subtitle]
 */
export default function StatCard({ label, value, icon: Icon, iconColor = '#2563EB', iconBg = '#EFF6FF', trend, trendLabel, loading, subtitle, onClick }) {
  const trendPositive = trend > 0;
  const trendNeutral = trend === 0 || trend === undefined;

  if (loading) {
    return (
      <div className="card" style={{ padding: '20px 24px' }}>
        <div className="skeleton" style={{ width: 36, height: 36, borderRadius: 10, marginBottom: 16 }} />
        <div className="skeleton" style={{ width: '60%', height: 14, borderRadius: 6, marginBottom: 8 }} />
        <div className="skeleton" style={{ width: '40%', height: 28, borderRadius: 6 }} />
      </div>
    );
  }

  return (
    <motion.div
      className="card"
      style={{ padding: '20px 24px', cursor: onClick ? 'pointer' : 'default' }}
      whileHover={onClick ? { y: -2 } : {}}
      onClick={onClick}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          {Icon && <Icon size={20} color={iconColor} strokeWidth={1.8} />}
        </div>
        {!trendNeutral && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: 12, fontWeight: 600, color: trendPositive ? '#10B981' : '#EF4444' }}>
            {trendPositive ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
            {Math.abs(trend)}%
          </div>
        )}
      </div>
      <div style={{ fontSize: 12, color: '#6B7280', fontWeight: 500, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 800, color: '#111827', lineHeight: 1.2 }}>{value ?? '—'}</div>
      {subtitle && <div style={{ fontSize: 12, color: '#9CA3AF', marginTop: 4 }}>{subtitle}</div>}
      {trendLabel && !trendNeutral && (
        <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 4 }}>{trendLabel}</div>
      )}
    </motion.div>
  );
}
