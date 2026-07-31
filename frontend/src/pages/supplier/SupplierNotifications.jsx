import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, CheckCheck, Search, Filter, Truck, AlertTriangle, Package, Star, MessageSquare, ShieldCheck, Check, X } from 'lucide-react';
import PageHeader from '../../components/supplier/shared/PageHeader';
import StatusBadge from '../../components/supplier/shared/StatusBadge';
import EmptyState from '../../components/supplier/shared/EmptyState';
import { markNotificationRead, markAllNotificationsRead } from '../../services/supplierApi';

const CATEGORIES = [
  { id: 'all', label: 'All', icon: Bell },
  { id: 'alerts', label: 'Risk Alerts', icon: AlertTriangle },
  { id: 'approvals', label: 'Approvals', icon: ShieldCheck },
  { id: 'shipments', label: 'Shipments', icon: Truck },
  { id: 'inventory', label: 'Inventory', icon: Package },
  { id: 'recommendations', label: 'Recommendations', icon: Star },
  { id: 'admin', label: 'Admin', icon: MessageSquare },
];

const TYPE_CONFIG = {
  alerts: { icon: AlertTriangle, color: '#EF4444', bg: '#FEF2F2' },
  approvals: { icon: ShieldCheck, color: '#10B981', bg: '#ECFDF5' },
  shipments: { icon: Truck, color: '#2563EB', bg: '#EFF6FF' },
  inventory: { icon: Package, color: '#F59E0B', bg: '#FFFBEB' },
  recommendations: { icon: Star, color: '#7C3AED', bg: '#F5F3FF' },
  admin: { icon: MessageSquare, color: '#6B7280', bg: '#F3F4F6' },
};

function NotificationItem({ notif, onMarkRead }) {
  const cfg = TYPE_CONFIG[notif.type] || TYPE_CONFIG.admin;
  const Icon = cfg.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }}
      style={{ display: 'flex', gap: 14, padding: '14px 18px', background: notif.read ? 'transparent' : '#FAFBFF', borderBottom: '1px solid #F3F4F6', transition: 'background 0.2s', position: 'relative' }}
      onMouseEnter={(e) => { e.currentTarget.style.background = '#F9FAFB'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = notif.read ? 'transparent' : '#FAFBFF'; }}
    >
      {!notif.read && <div style={{ position: 'absolute', left: 6, top: '50%', transform: 'translateY(-50%)', width: 6, height: 6, borderRadius: '50%', background: '#2563EB' }} />}

      <div style={{ width: 38, height: 38, borderRadius: 10, background: cfg.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={18} color={cfg.color} />
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, marginBottom: 3 }}>
          <div style={{ fontSize: 13.5, fontWeight: notif.read ? 500 : 700, color: '#111827', lineHeight: 1.4 }}>{notif.title || 'Notification'}</div>
          <div style={{ fontSize: 11, color: '#9CA3AF', whiteSpace: 'nowrap', flexShrink: 0 }}>{notif.time || 'Just now'}</div>
        </div>
        <div style={{ fontSize: 13, color: '#6B7280', lineHeight: 1.5 }}>{notif.body || 'No details provided.'}</div>
        {notif.type && (
          <div style={{ marginTop: 8 }}>
            <StatusBadge status="info" label={CATEGORIES.find((c) => c.id === notif.type)?.label || notif.type} />
          </div>
        )}
      </div>

      {!notif.read && (
        <button onClick={() => onMarkRead(notif.id)}
          style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px', border: '1px solid #E5E7EB', borderRadius: 6, fontSize: 11, background: 'white', color: '#6B7280', cursor: 'pointer', fontWeight: 500, alignSelf: 'center' }}
          onMouseEnter={(e) => { e.currentTarget.style.background = '#ECFDF5'; e.currentTarget.style.color = '#10B981'; e.currentTarget.style.borderColor = '#10B981'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'white'; e.currentTarget.style.color = '#6B7280'; e.currentTarget.style.borderColor = '#E5E7EB'; }}>
          <Check size={11} /> Mark read
        </button>
      )}
    </motion.div>
  );
}

export default function SupplierNotifications() {
  const [activeTab, setActiveTab] = useState('all');
  const [query, setQuery] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [markingAll, setMarkingAll] = useState(false);

  const unread = notifications.filter((n) => !n.read).length;

  const filtered = notifications.filter((n) => {
    const matchTab = activeTab === 'all' || n.type === activeTab;
    const matchQ = !query || n.title?.toLowerCase().includes(query.toLowerCase()) || n.body?.toLowerCase().includes(query.toLowerCase());
    return matchTab && matchQ;
  });

  async function handleMarkRead(id) {
    await markNotificationRead(id);
    setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, read: true } : n));
  }

  async function handleMarkAllRead() {
    setMarkingAll(true);
    await markAllNotificationsRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    setMarkingAll(false);
  }

  return (
    <div>
      <PageHeader
        title="Notifications"
        description="Stay informed about alerts, approvals, shipment updates, and AI recommendations"
        actions={
          unread > 0 && (
            <button onClick={handleMarkAllRead} disabled={markingAll}
              style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '8px 16px', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 13, fontWeight: 600, background: 'white', color: '#374151', cursor: markingAll ? 'not-allowed' : 'pointer' }}>
              <CheckCheck size={14} />{markingAll ? 'Marking…' : `Mark All Read (${unread})`}
            </button>
          )
        }
      />

      {/* Category tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, overflowX: 'auto', paddingBottom: 4 }}>
        {CATEGORIES.map(({ id, label, icon: Icon }) => {
          const count = id === 'all' ? unread : notifications.filter((n) => n.type === id && !n.read).length;
          return (
            <button key={id} onClick={() => setActiveTab(id)}
              style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 8, border: `1.5px solid ${activeTab === id ? '#2563EB' : '#E5E7EB'}`, background: activeTab === id ? '#EFF6FF' : 'white', color: activeTab === id ? '#2563EB' : '#6B7280', fontSize: 13, fontWeight: activeTab === id ? 700 : 400, cursor: 'pointer', whiteSpace: 'nowrap', transition: 'all 0.15s' }}>
              <Icon size={13} />
              {label}
              {count > 0 && <span style={{ background: '#EF4444', color: 'white', borderRadius: 10, fontSize: 10, fontWeight: 700, padding: '1px 6px' }}>{count}</span>}
            </button>
          );
        })}
      </div>

      {/* Search */}
      <div style={{ position: 'relative', maxWidth: 360, marginBottom: 16 }}>
        <Search size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#9CA3AF', pointerEvents: 'none' }} />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search notifications…"
          style={{ width: '100%', paddingLeft: 36, paddingRight: 14, paddingTop: 9, paddingBottom: 9, border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 13, outline: 'none', boxSizing: 'border-box' }}
          onFocus={(e) => e.target.style.borderColor = '#2563EB'} onBlur={(e) => e.target.style.borderColor = '#E5E7EB'} />
      </div>

      {/* Notification list */}
      <div className="card" style={{ overflow: 'hidden' }}>
        {filtered.length === 0 ? (
          <EmptyState type="inbox" title="No notifications" description="You're all caught up! Notifications about alerts, shipments, and approvals will appear here." />
        ) : (
          filtered.map((notif) => <NotificationItem key={notif.id} notif={notif} onMarkRead={handleMarkRead} />)
        )}
      </div>
    </div>
  );
}
