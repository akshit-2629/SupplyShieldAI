import { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { SupplierAuthProvider, useSupplierAuth } from '../context/SupplierAuthContext';
import SupplierSidebar from '../components/supplier/layout/SupplierSidebar';
import SupplierNavbar from '../components/supplier/layout/SupplierNavbar';
import { getSetupStatus } from '../services/supplierApi';

// ── Inner layout with setup guard ─────────────────────────────────────────────
function SupplierLayoutInner() {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [setupChecked, setSetupChecked] = useState(false);
  const location = useLocation();
  const navigate  = useNavigate();
  const { supplierUser, loading: authLoading } = useSupplierAuth();

  useEffect(() => {
    // Don't check while auth is still loading
    if (authLoading) return;

    // If not authenticated, redirect to login page immediately
    if (!supplierUser) {
      navigate('/supplier/login', { replace: true });
      return;
    }

    if (location.pathname === '/supplier/setup') {
      setSetupChecked(true);
      return;
    }

    let cancelled = false;
    getSetupStatus()
      .then((res) => {
        if (cancelled) return;
        const status = res?.data ?? res;
        if (status && !status.is_complete) {
          navigate('/supplier/setup', { replace: true });
        } else {
          setSetupChecked(true);
        }
      })
      .catch(() => {
        // If setup check fails (network / DB not ready), allow through
        if (!cancelled) setSetupChecked(true);
      });

    return () => { cancelled = true; };
  }, [supplierUser, authLoading, location.pathname, navigate]);

  // While checking setup (only on first load), show a minimal loading screen
  if ((authLoading || !setupChecked) && location.pathname !== '/supplier/setup') {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F9FAFB' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: 40, height: 40, borderRadius: '50%', border: '3px solid #E5E7EB', borderTopColor: '#10B981', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <div style={{ fontSize: 13, color: '#6B7280' }}>Verifying portal access…</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#F9FAFB' }}>
      {/* Desktop sidebar — hidden on setup page */}
      {location.pathname !== '/supplier/setup' && (
        <div style={{ display: 'flex' }} className="hidden-mobile-flex">
          <SupplierSidebar />
        </div>
      )}

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {mobileSidebarOpen && location.pathname !== '/supplier/setup' && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setMobileSidebarOpen(false)}
              style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', zIndex: 40 }}
            />
            <motion.div
              initial={{ x: -248 }} animate={{ x: 0 }} exit={{ x: -248 }}
              transition={{ duration: 0.25 }}
              style={{ position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 50 }}
            >
              <SupplierSidebar />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        {location.pathname !== '/supplier/setup' && (
          <SupplierNavbar mobileSidebarOpen={mobileSidebarOpen} setMobileSidebarOpen={setMobileSidebarOpen} />
        )}
        <main style={{ flex: 1, overflowY: 'auto', padding: location.pathname === '/supplier/setup' ? 0 : '24px' }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              style={{ height: '100%' }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

// ── Outer wrapper with auth context ──────────────────────────────────────────
export default function SupplierLayout() {
  return (
    <SupplierAuthProvider>
      <SupplierLayoutInner />
    </SupplierAuthProvider>
  );
}
