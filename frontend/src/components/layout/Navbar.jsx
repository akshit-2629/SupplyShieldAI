import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Search, ChevronDown, User, Settings, LogOut, Menu, X, Command } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { useAuth } from '../../context/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';

const breadcrumbMap = {
  '/dashboard':          ['Dashboard'],
  '/disruption-monitor': ['Disruption Monitor'],
  '/risk-map':           ['Global Risk Map'],
  '/knowledge-graph':    ['Knowledge Graph'],
  '/suppliers':          ['Suppliers'],
  '/incidents':          ['Incidents'],
  '/inventory':          ['Inventory Impact'],
  '/recommendations':    ['Recommendations'],
  '/orchestration':      ['AI Orchestration'],
  '/reports':            ['Reports'],
  '/alerts':             ['Alert Center'],
  '/settings':           ['Settings'],
};

export default function Navbar({ mobileSidebarOpen, setMobileSidebarOpen }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { setCommandPaletteOpen } = useAppStore();
  const { user, signOut } = useAuth();
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);

  const crumbs = breadcrumbMap[location.pathname] || [];
  // Live unread count from backend risk assessments (HIGH/CRITICAL = actionable)
  const { data: riskData } = useQuery({ queryKey: ['navbar-alerts'], queryFn: () => api.get('/risk/assessments'), staleTime: 60_000 });
  const riskAlerts = Array.isArray(riskData) ? riskData : riskData?.assessments || [];
  const unread = riskAlerts.filter(a => ['HIGH', 'CRITICAL'].includes(a.risk_level)).length;

  // Derive display name and initials from Supabase user
  const displayName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User';
  const displayEmail = user?.email || '';
  const initials = displayName
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  async function handleLogout() {
    setProfileOpen(false);
    await signOut();
    navigate('/login', { replace: true });
  }

  return (
    <header style={{ height: 56, background: 'white', borderBottom: '1px solid #E5E7EB', display: 'flex', alignItems: 'center', padding: '0 20px', gap: 12, position: 'sticky', top: 0, zIndex: 30, flexShrink: 0 }}>
      {/* Mobile menu toggle */}
      <button className="md:hidden" onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)} style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 4, borderRadius: 6, color: '#6B7280' }}>
        {mobileSidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Breadcrumb */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 12, color: '#9CA3AF' }}>SupplyShield AI</span>
        {crumbs.map((c, i) => (
          <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 12, color: '#D1D5DB' }}>/</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>{c}</span>
          </span>
        ))}
      </div>

      {/* Search trigger */}
      <button
        onClick={() => setCommandPaletteOpen(true)}
        style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#F5F5F5', border: '1px solid #E5E7EB', borderRadius: 8, padding: '6px 12px', cursor: 'pointer', fontSize: 13, color: '#9CA3AF', transition: 'all 0.15s' }}
        onMouseEnter={e => e.currentTarget.style.background = '#EFEFEF'}
        onMouseLeave={e => e.currentTarget.style.background = '#F5F5F5'}
      >
        <Search size={14} />
        <span>Search...</span>
        <span style={{ marginLeft: 8, display: 'flex', alignItems: 'center', gap: 2, background: 'white', border: '1px solid #E5E7EB', borderRadius: 4, padding: '1px 5px', fontSize: 11 }}>
          <Command size={10} /> K
        </span>
      </button>

      {/* Notifications */}
      <div style={{ position: 'relative' }}>
        <button
          onClick={() => { setNotifOpen(!notifOpen); setProfileOpen(false); }}
          style={{ position: 'relative', background: 'none', border: 'none', cursor: 'pointer', padding: 6, borderRadius: 8, color: '#6B7280', display: 'flex', alignItems: 'center', transition: 'background 0.15s' }}
          onMouseEnter={e => e.currentTarget.style.background = '#F5F5F5'}
          onMouseLeave={e => e.currentTarget.style.background = 'none'}
        >
          <Bell size={18} />
          {unread > 0 && (
            <span style={{ position: 'absolute', top: 3, right: 3, width: 16, height: 16, background: '#DC2626', borderRadius: '50%', fontSize: 9, color: 'white', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid white' }}>
              {unread}
            </span>
          )}
        </button>

        <AnimatePresence>
          {notifOpen && (
            <motion.div initial={{ opacity: 0, y: -8, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -8, scale: 0.96 }} transition={{ duration: 0.15 }}
              style={{ position: 'absolute', top: '100%', right: 0, marginTop: 8, width: 360, background: 'white', border: '1px solid #E5E7EB', borderRadius: 12, boxShadow: '0 10px 40px rgba(0,0,0,0.1)', overflow: 'hidden', zIndex: 50 }}
            >
              <div style={{ padding: '14px 16px', borderBottom: '1px solid #F3F4F6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, fontSize: 14 }}>Notifications</span>
                <span style={{ background: '#FEE2E2', color: '#991B1B', fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 10 }}>{unread} new</span>
              </div>
              <div style={{ maxHeight: 380, overflowY: 'auto' }}>
                {riskAlerts.filter(a => ['HIGH', 'CRITICAL'].includes(a.risk_level)).slice(0, 5).map(alert => (
                  <div key={alert.assessment_id} onClick={() => { setNotifOpen(false); navigate('/alerts'); }}
                    style={{ padding: '12px 16px', borderBottom: '1px solid #F9FAFB', cursor: 'pointer', background: '#FAFBFF', transition: 'background 0.1s' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#F5F5F5'}
                    onMouseLeave={e => e.currentTarget.style.background = '#FAFBFF'}
                  >
                    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                      <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#DC2626', marginTop: 4, flexShrink: 0 }} />
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 500, color: '#111827', marginBottom: 2 }}>{alert.title || 'Risk Alert'}</div>
                        <div style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.4 }}>{alert.risk_level} · Score {(alert.risk_score || 0).toFixed(0)}/100</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ padding: '10px 16px', borderTop: '1px solid #F3F4F6' }}>
                <button onClick={() => { setNotifOpen(false); navigate('/alerts'); }} style={{ width: '100%', background: 'none', border: 'none', color: '#2563EB', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>View all alerts →</button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Profile */}
      <div style={{ position: 'relative' }}>
        <button
          onClick={() => { setProfileOpen(!profileOpen); setNotifOpen(false); }}
          style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'none', border: '1px solid #E5E7EB', borderRadius: 8, padding: '5px 10px', cursor: 'pointer', transition: 'all 0.15s' }}
          onMouseEnter={e => e.currentTarget.style.background = '#F5F5F5'}
          onMouseLeave={e => e.currentTarget.style.background = 'none'}
        >
          <div style={{ width: 26, height: 26, borderRadius: '50%', background: 'linear-gradient(135deg, #2563EB, #7C3AED)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <span style={{ fontSize: 10, fontWeight: 700, color: 'white' }}>{initials}</span>
          </div>
          <div style={{ textAlign: 'left', maxWidth: 120, overflow: 'hidden' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#111827', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{displayName}</div>
            <div style={{ fontSize: 10, color: '#9CA3AF', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{displayEmail}</div>
          </div>
          <ChevronDown size={13} color="#9CA3AF" />
        </button>

        <AnimatePresence>
          {profileOpen && (
            <motion.div initial={{ opacity: 0, y: -8, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -8, scale: 0.96 }} transition={{ duration: 0.15 }}
              style={{ position: 'absolute', top: '100%', right: 0, marginTop: 8, width: 200, background: 'white', border: '1px solid #E5E7EB', borderRadius: 10, boxShadow: '0 8px 30px rgba(0,0,0,0.1)', overflow: 'hidden', zIndex: 50 }}
            >
              {[
                { label: 'Profile', icon: User, action: () => navigate('/settings') },
                { label: 'Settings', icon: Settings, action: () => navigate('/settings') },
                { label: 'Logout', icon: LogOut, action: handleLogout, danger: true },
              ].map(item => (
                <button key={item.label} onClick={() => { setProfileOpen(false); item.action(); }}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', background: 'none', border: 'none', fontSize: 13, color: item.danger ? '#EF4444' : '#374151', cursor: 'pointer', textAlign: 'left', transition: 'background 0.1s' }}
                  onMouseEnter={e => e.currentTarget.style.background = item.danger ? '#FEF2F2' : '#F5F5F5'}
                  onMouseLeave={e => e.currentTarget.style.background = 'none'}
                >
                  <item.icon size={15} />
                  {item.label}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
}
