import { NavLink, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Building2, Factory, Package, Clock,
  Truck, AlertTriangle, BarChart3, Star, Bell, LifeBuoy,
  Settings, LogOut, ShieldCheck, ChevronLeft, ChevronRight,
  Boxes, ClipboardCheck, FolderOpen
} from 'lucide-react';
import { useSupplierStore } from '../../../store/supplierStore';
import { useSupplierAuth } from '../../../context/SupplierAuthContext';

const NAV_ITEMS = [
  { to: '/supplier/dashboard',    label: 'Dashboard',           icon: LayoutDashboard },
  { to: '/supplier/profile',      label: 'Company Profile',     icon: Building2 },
  { to: '/supplier/production',   label: 'Production Capacity', icon: Factory },
  { to: '/supplier/inventory',    label: 'Inventory',           icon: Boxes },
  { to: '/supplier/lead-time',    label: 'Lead Time',           icon: Clock },
  { to: '/supplier/shipments',    label: 'Shipments',           icon: Truck },
  { to: '/supplier/incidents',    label: 'Incident Reporting',  icon: AlertTriangle },
  { to: '/supplier/forecast',     label: 'Capacity Forecast',   icon: BarChart3 },
  { to: '/supplier/quality',      label: 'Quality Management',  icon: ClipboardCheck },
  { to: '/supplier/documents',    label: 'Document Center',     icon: FolderOpen },
  { to: '/supplier/metrics',      label: 'AI Performance',      icon: Star },
  { to: '/supplier/notifications',label: 'Notifications',       icon: Bell, badge: true },
  { to: '/supplier/support',      label: 'Support Center',      icon: LifeBuoy },
  { to: '/supplier/settings',     label: 'Settings',            icon: Settings },
];

export default function SupplierSidebar() {
  const { sidebarOpen, toggleSidebar, unreadCount } = useSupplierStore();
  const { signOut, supplierUser } = useSupplierAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await signOut();
    navigate('/role-select', { replace: true });
  }

  const companyName = supplierUser?.user_metadata?.companyName || 'My Company';
  const contactName = supplierUser?.user_metadata?.contactName || supplierUser?.email || '';

  return (
    <motion.aside
      animate={{ width: sidebarOpen ? 248 : 64 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      style={{
        minHeight: '100vh', background: '#fff',
        borderRight: '1px solid #E5E7EB',
        display: 'flex', flexDirection: 'column',
        position: 'relative', zIndex: 20, flexShrink: 0,
        overflow: 'hidden',
      }}
    >
      {/* Logo */}
      <div style={{ padding: '18px 14px', borderBottom: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', gap: 10, overflow: 'hidden' }}>
        <div style={{ width: 34, height: 34, background: 'linear-gradient(135deg, #10B981, #059669)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <ShieldCheck size={18} color="white" strokeWidth={2} />
        </div>
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} transition={{ duration: 0.15 }}>
              <div style={{ fontSize: 13.5, fontWeight: 700, color: '#111827', whiteSpace: 'nowrap' }}>SupplyShield</div>
              <div style={{ fontSize: 10, color: '#10B981', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Supplier Portal</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Company badge */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ padding: '12px 14px', borderBottom: '1px solid #F3F4F6' }}
          >
            <div style={{ background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 8, padding: '10px 12px' }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: '#111827', marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{companyName}</div>
              <div style={{ fontSize: 11, color: '#6B7280', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{contactName}</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '10px 8px', overflowY: 'auto', overflowX: 'hidden' }}>
        {NAV_ITEMS.map(({ to, label, icon: Icon, badge }) => (
          <NavLink key={to} to={to}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 10px', borderRadius: 7, marginBottom: 2,
              textDecoration: 'none', transition: 'all 0.15s',
              background: isActive ? '#ECFDF5' : 'transparent',
              color: isActive ? '#059669' : '#6B7280',
              fontWeight: isActive ? 600 : 400,
              fontSize: 13.5, overflow: 'hidden', whiteSpace: 'nowrap',
              position: 'relative',
            })}
            title={!sidebarOpen ? label : ''}
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div layoutId="supplier-nav-indicator"
                    style={{ position: 'absolute', left: 0, top: 4, bottom: 4, width: 3, background: '#10B981', borderRadius: '0 2px 2px 0' }}
                  />
                )}
                <Icon size={17} strokeWidth={isActive ? 2.2 : 1.8} style={{ flexShrink: 0 }} />
                <AnimatePresence>
                  {sidebarOpen && (
                    <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }} style={{ flex: 1 }}>
                      {label}
                    </motion.span>
                  )}
                </AnimatePresence>
                {badge && unreadCount > 0 && sidebarOpen && (
                  <span style={{ background: '#EF4444', color: 'white', borderRadius: 10, fontSize: 10, fontWeight: 700, padding: '1px 6px', flexShrink: 0 }}>
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
                {badge && unreadCount > 0 && !sidebarOpen && (
                  <span style={{ position: 'absolute', top: 6, right: 8, width: 7, height: 7, background: '#EF4444', borderRadius: '50%' }} />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div style={{ padding: '10px 8px', borderTop: '1px solid #F3F4F6' }}>
        <button onClick={handleLogout}
          style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', borderRadius: 7, border: 'none', background: 'transparent', color: '#EF4444', fontSize: 13.5, cursor: 'pointer', transition: 'background 0.15s', overflow: 'hidden', whiteSpace: 'nowrap' }}
          onMouseEnter={(e) => { e.currentTarget.style.background = '#FEF2F2'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
          title={!sidebarOpen ? 'Logout' : ''}
        >
          <LogOut size={17} strokeWidth={1.8} style={{ flexShrink: 0 }} />
          <AnimatePresence>
            {sidebarOpen && (
              <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
                Sign Out
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>

      {/* Collapse toggle */}
      <button onClick={toggleSidebar}
        style={{ position: 'absolute', top: 22, right: -12, width: 24, height: 24, background: 'white', border: '1px solid #E5E7EB', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', zIndex: 10, boxShadow: '0 1px 4px rgba(0,0,0,0.1)', transition: 'all 0.15s' }}
        onMouseEnter={(e) => { e.currentTarget.style.background = '#F3F4F6'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'white'; }}
      >
        {sidebarOpen ? <ChevronLeft size={13} color="#6B7280" /> : <ChevronRight size={13} color="#6B7280" />}
      </button>
    </motion.aside>
  );
}
