import { useNavigate, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

const ROUTE_LABELS = {
  dashboard: 'Dashboard',
  profile: 'Company Profile',
  production: 'Production Capacity',
  inventory: 'Inventory Management',
  'lead-time': 'Lead Time',
  shipments: 'Shipment Management',
  incidents: 'Incident Reporting',
  forecast: 'Capacity Forecast',
  metrics: 'Performance Metrics',
  notifications: 'Notifications',
  support: 'Support Center',
  settings: 'Settings',
};

/**
 * PageHeader — breadcrumb + title + optional right-side action slot.
 * @param {string} title - main page title
 * @param {string} [description] - subtitle text
 * @param {React.ReactNode} [actions] - right-side buttons/badges
 */
export default function PageHeader({ title, description, actions }) {
  const location = useLocation();
  const segments = location.pathname.replace('/supplier/', '').split('/').filter(Boolean);

  return (
    <div style={{ marginBottom: 28 }}>
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#6B7280', fontSize: 12 }}>
          <Home size={13} />
          <span>Supplier Portal</span>
        </div>
        {segments.map((seg, i) => (
          <div key={seg} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <ChevronRight size={13} color="#D1D5DB" />
            <span style={{ fontSize: 12, color: i === segments.length - 1 ? '#111827' : '#6B7280', fontWeight: i === segments.length - 1 ? 600 : 400 }}>
              {ROUTE_LABELS[seg] || seg}
            </span>
          </div>
        ))}
      </div>

      {/* Title row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: description ? 4 : 0 }}>{title}</h1>
          {description && <p style={{ fontSize: 13.5, color: '#6B7280', maxWidth: 600 }}>{description}</p>}
        </div>
        {actions && <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>{actions}</div>}
      </div>
    </div>
  );
}
