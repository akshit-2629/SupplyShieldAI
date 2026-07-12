import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck } from 'lucide-react';

/**
 * ProtectedRoute guards all dashboard routes.
 * - While auth state is loading → shows a full-page spinner
 * - No authenticated user → redirects to /login
 * - Authenticated user → renders the child route via <Outlet />
 */
export default function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        background: '#F9FAFB',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 16,
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
            Verifying session...
          </span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
