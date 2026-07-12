import { NavLink, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, AlertTriangle, Globe, Network, Building2,
  FileSearch, Package, Stars, Cpu, FileText, Bell, Settings,
  LogOut, ShieldCheck, ChevronLeft, ChevronRight
} from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { useAuth } from '../../context/AuthContext';

const navItems = [
  { to: '/dashboard',          label: 'Dashboard',         icon: LayoutDashboard },
  { to: '/disruption-monitor', label: 'Disruption Monitor', icon: AlertTriangle },
  { to: '/risk-map',           label: 'Global Risk Map',   icon: Globe },
  { to: '/knowledge-graph',    label: 'Knowledge Graph',   icon: Network },
  { to: '/suppliers',          label: 'Suppliers',         icon: Building2 },
  { to: '/incidents',          label: 'Incidents',         icon: FileSearch },
  { to: '/inventory',          label: 'Inventory Impact',  icon: Package },
  { to: '/recommendations',    label: 'Recommendations',   icon: Stars },
  { to: '/orchestration',      label: 'AI Orchestration',  icon: Cpu },
  { to: '/reports',            label: 'Reports',           icon: FileText },
  { to: '/alerts',             label: 'Alerts',            icon: Bell },
  { to: '/settings',           label: 'Settings',          icon: Settings },
];

export default function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useAppStore();
  const { signOut } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await signOut();
    navigate('/login', { replace: true });
  }

  return (
    <motion.aside
      animate={{ width: sidebarOpen ? 240 : 64 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      style={{ minHeight: '100vh', background: '#fff', borderRight: '1px solid #E5E7EB', display: 'flex', flexDirection: 'column', position: 'relative', zIndex: 20, flexShrink: 0 }}
    >
      {/* Logo */}
      <div style={{ padding: '20px 16px', borderBottom: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', gap: 10, overflow: 'hidden' }}>
        <div style={{ width: 32, height: 32, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <ShieldCheck size={18} color="white" strokeWidth={2} />
        </div>
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }} transition={{ duration: 0.15 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', whiteSpace: 'nowrap' }}>SupplyShield</div>
              <div style={{ fontSize: 10, color: '#6B7280', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>AI Platform</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Nav Items */}
      <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto', overflowX: 'hidden' }}>
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 10px', borderRadius: 7, marginBottom: 2,
              textDecoration: 'none', transition: 'all 0.15s',
              background: isActive ? '#EFF6FF' : 'transparent',
              color: isActive ? '#2563EB' : '#6B7280',
              fontWeight: isActive ? 600 : 400,
              fontSize: 13.5,
              overflow: 'hidden', whiteSpace: 'nowrap',
            })}
            title={!sidebarOpen ? label : ''}
          >
            {({ isActive }) => (
              <>
                <Icon size={17} strokeWidth={isActive ? 2.2 : 1.8} style={{ flexShrink: 0 }} />
                <AnimatePresence>
                  {sidebarOpen && (
                    <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
                      {label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom: Logout */}
      <div style={{ padding: '12px 8px', borderTop: '1px solid #F3F4F6' }}>
        <button
          onClick={handleLogout}
          style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', borderRadius: 7, border: 'none', background: 'transparent', color: '#EF4444', fontSize: 13.5, cursor: 'pointer', transition: 'background 0.15s', overflow: 'hidden', whiteSpace: 'nowrap' }}
          onMouseEnter={e => e.currentTarget.style.background = '#FEF2F2'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          title={!sidebarOpen ? 'Logout' : ''}
        >
          <LogOut size={17} strokeWidth={1.8} style={{ flexShrink: 0 }} />
          <AnimatePresence>
            {sidebarOpen && (
              <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
                Logout
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={toggleSidebar}
        style={{
          position: 'absolute', top: 22, right: -12, width: 24, height: 24,
          background: 'white', border: '1px solid #E5E7EB', borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', zIndex: 10, boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
          transition: 'all 0.15s',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = '#F3F4F6'; }}
        onMouseLeave={e => { e.currentTarget.style.background = 'white'; }}
      >
        {sidebarOpen ? <ChevronLeft size={13} color="#6B7280" /> : <ChevronRight size={13} color="#6B7280" />}
      </button>
    </motion.aside>
  );
}
