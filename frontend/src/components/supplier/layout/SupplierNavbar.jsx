import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, Search, Bell, ChevronDown, User, Settings, LogOut, ShieldCheck, Building2, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useSupplierStore } from '../../../store/supplierStore';
import { useSupplierAuth } from '../../../context/SupplierAuthContext';

export default function SupplierNavbar({ setMobileSidebarOpen, mobileSidebarOpen }) {
  const { unreadCount, searchQuery, setSearchQuery } = useSupplierStore();
  const { supplierUser, signOut } = useSupplierAuth();
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);

  const companyName = supplierUser?.user_metadata?.companyName || 'My Company';
  const contactName = supplierUser?.user_metadata?.contactName || supplierUser?.email || 'Supplier';
  const initials = contactName.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase();

  async function handleSignOut() {
    setProfileOpen(false);
    await signOut();
    navigate('/role-select', { replace: true });
  }

  return (
    <header style={{ height: 60, background: 'white', borderBottom: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', padding: '0 20px', gap: 12, position: 'sticky', top: 0, zIndex: 30, flexShrink: 0 }}>
      {/* Mobile menu button */}
      <button onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        className="md:hidden"
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6B7280', padding: 4, display: 'none' }}>
        {mobileSidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Search */}
      <div style={{ flex: 1, maxWidth: 380, position: 'relative' }}>
        <Search size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#9CA3AF', pointerEvents: 'none' }} />
        <input
          value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search your portal..."
          onFocus={() => setSearchFocused(true)} onBlur={() => setSearchFocused(false)}
          style={{ width: '100%', paddingLeft: 36, paddingRight: 14, paddingTop: 8, paddingBottom: 8, border: `1px solid ${searchFocused ? '#10B981' : '#E5E7EB'}`, borderRadius: 8, fontSize: 13.5, outline: 'none', background: '#F9FAFB', transition: 'border 0.2s, background 0.2s', boxSizing: 'border-box' }}
        />
      </div>

      <div style={{ flex: 1 }} />

      {/* Supplier badge */}
      <div className="hidden-mobile" style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: 20, padding: '4px 12px' }}>
        <Building2 size={12} color="#10B981" />
        <span style={{ fontSize: 11.5, fontWeight: 600, color: '#059669' }}>Supplier</span>
      </div>

      {/* Notifications */}
      <button onClick={() => navigate('/supplier/notifications')}
        style={{ position: 'relative', background: 'none', border: 'none', cursor: 'pointer', color: '#6B7280', padding: 8, borderRadius: 8, transition: 'background 0.15s' }}
        onMouseEnter={(e) => { e.currentTarget.style.background = '#F3F4F6'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span style={{ position: 'absolute', top: 4, right: 4, width: 16, height: 16, background: '#EF4444', borderRadius: '50%', fontSize: 9, fontWeight: 700, color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Profile menu */}
      <div style={{ position: 'relative' }}>
        <button onClick={() => setProfileOpen(!profileOpen)}
          style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '5px 10px', borderRadius: 8, border: '1px solid #E5E7EB', background: 'white', cursor: 'pointer', transition: 'background 0.15s' }}
          onMouseEnter={(e) => { e.currentTarget.style.background = '#F9FAFB'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'white'; }}
        >
          <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'linear-gradient(135deg, #10B981, #059669)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: 'white' }}>
            {initials || <User size={14} />}
          </div>
          <div className="hidden-mobile" style={{ textAlign: 'left' }}>
            <div style={{ fontSize: 12.5, fontWeight: 600, color: '#111827', lineHeight: 1.2, maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{contactName}</div>
            <div style={{ fontSize: 10.5, color: '#6B7280', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{companyName}</div>
          </div>
          <ChevronDown size={13} color="#9CA3AF" style={{ transition: 'transform 0.2s', transform: profileOpen ? 'rotate(180deg)' : 'none' }} />
        </button>

        <AnimatePresence>
          {profileOpen && (
            <>
              <div style={{ position: 'fixed', inset: 0, zIndex: 40 }} onClick={() => setProfileOpen(false)} />
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -4 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -4 }}
                transition={{ duration: 0.15 }}
                style={{ position: 'absolute', right: 0, top: 'calc(100% + 8px)', width: 220, background: 'white', border: '1px solid #E5E7EB', borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.12)', overflow: 'hidden', zIndex: 50 }}
              >
                <div style={{ padding: '14px 16px', borderBottom: '1px solid #F3F4F6' }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>{contactName}</div>
                  <div style={{ fontSize: 11, color: '#6B7280', marginTop: 2 }}>{supplierUser?.email}</div>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginTop: 6, background: '#ECFDF5', borderRadius: 10, padding: '2px 8px' }}>
                    <ShieldCheck size={10} color="#10B981" />
                    <span style={{ fontSize: 10, fontWeight: 600, color: '#059669' }}>Supplier Account</span>
                  </div>
                </div>
                {[
                  { icon: User, label: 'My Profile', to: '/supplier/profile' },
                  { icon: Settings, label: 'Settings', to: '/supplier/settings' },
                ].map(({ icon: Icon, label, to }) => (
                  <button key={label} onClick={() => { navigate(to); setProfileOpen(false); }}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px', border: 'none', background: 'transparent', fontSize: 13, color: '#374151', cursor: 'pointer', textAlign: 'left' }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = '#F9FAFB'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                  >
                    <Icon size={15} color="#6B7280" />
                    {label}
                  </button>
                ))}
                <div style={{ borderTop: '1px solid #F3F4F6' }}>
                  <button onClick={handleSignOut}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px', border: 'none', background: 'transparent', fontSize: 13, color: '#EF4444', cursor: 'pointer', textAlign: 'left' }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = '#FEF2F2'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                  >
                    <LogOut size={15} />
                    Sign Out
                  </button>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
}
