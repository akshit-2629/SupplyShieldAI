import { useState, useEffect } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck } from 'lucide-react';
import { getSetupStatus } from '../../services/manufacturerApi';

/**
 * ProtectedRoute — guards all Manufacturer / Admin dashboard routes.
 *
 * Flow:
 *   1. Wait for Supabase auth to resolve (loading spinner)
 *   2. No authenticated user → /login
 *   3. User is a supplier (role=supplier) → /supplier/login (wrong portal)
 *   4. Setup not complete → /setup wizard
 *   5. All clear → render <Outlet />
 *
 * The /setup route is placed OUTSIDE this guard so the wizard
 * is never blocked by a redirect loop.
 *
 * ROLE ISOLATION: AuthContext already filters out supplier sessions,
 * but we add an explicit check here as a second layer of defense.
 */
export default function ProtectedRoute() {
  const { user, loading: authLoading } = useAuth();
  const location = useLocation();

  const [setupStatus,  setSetupStatus]  = useState(null);   // null = not yet checked
  const [setupLoading, setSetupLoading] = useState(false);
  const [setupError,   setSetupError]   = useState(false);

  useEffect(() => {
    if (!user || authLoading) return;

    setSetupLoading(true);
    setSetupError(false);
    getSetupStatus()
      .then((s) => setSetupStatus(s))
      .catch(() => {
        // Network error — do NOT redirect to /setup in a loop.
        // Mark as error and fall through to render the outlet
        // so the user isn't stuck in a redirect cycle.
        setSetupError(true);
        setSetupStatus({ complete: true, current_step: 1 }); // Treat as complete on error
      })
      .finally(() => setSetupLoading(false));
  }, [user, authLoading]);

  // ── Phase 1: Auth is still loading ──
  if (authLoading || (user && setupLoading && setupStatus === null)) {
    return (
      <div style={{
        minHeight: '100vh',
        background: '#F9FAFB',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 16,
      }}>
        <div style={{
          width: 56, height: 56,
          background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
          borderRadius: 16,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          animation: 'float 2s ease-in-out infinite',
        }}>
          <ShieldCheck size={28} color="white" strokeWidth={2} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 6, height: 6, borderRadius: '50%', background: '#2563EB',
            animation: 'pulse-ring 1.4s ease-out infinite',
          }} />
          <span style={{ fontSize: 14, color: '#6B7280', fontWeight: 500 }}>
            Verifying session…
          </span>
        </div>
      </div>
    );
  }

  // ── Phase 2: No user → login ──
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // ── Phase 3: Supplier trying to access manufacturer dashboard ──
  // Double-check even though AuthContext already handles this
  const role = user?.user_metadata?.role;
  if (role === 'supplier') {
    return <Navigate to="/supplier/login" replace />;
  }

  // ── Phase 4: Onboarding not complete → setup wizard ──
  // Guard against redirect loop: never redirect if already on /setup
  if (setupStatus && !setupStatus.complete && location.pathname !== '/setup') {
    return <Navigate to="/setup" replace />;
  }

  // ── Phase 5: All clear → render protected content ──
  return <Outlet />;
}
