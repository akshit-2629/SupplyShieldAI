import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useSupplierAuth } from '../../context/SupplierAuthContext';
import { supabase } from '../../lib/supabase';
import { ShieldCheck, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * SupplierProtectedRoute
 *
 * Guards all /supplier/* portal routes.
 * - Loading → full-page spinner
 * - Not authenticated → redirect to /supplier/login
 * - Authenticated but not approved → pending approval screen
 * - Authenticated + approved → render portal via <Outlet />
 */
export default function SupplierProtectedRoute() {
  const { supplierUser, isApproved, loading } = useSupplierAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: '#F9FAFB', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
        <div style={{ width: 56, height: 56, background: 'linear-gradient(135deg, #10B981, #059669)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', animation: 'float 2s ease-in-out infinite' }}>
          <ShieldCheck size={28} color="white" strokeWidth={2} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981', animation: 'pulse-ring 1.4s ease-out infinite' }} />
          <span style={{ fontSize: 14, color: '#6B7280', fontWeight: 500 }}>Verifying supplier session...</span>
        </div>
      </div>
    );
  }

  if (!supplierUser) {
    return <Navigate to="/supplier/login" state={{ from: location }} replace />;
  }

  // Check supplier role
  const role = supplierUser?.user_metadata?.role;
  if (role !== 'supplier') {
    return <Navigate to="/supplier/login" replace />;
  }

  // Pending approval screen
  if (!isApproved) {
    return (
      <div style={{ minHeight: '100vh', background: '#F9FAFB', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
        <div style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 20, padding: '48px 40px', maxWidth: 480, width: '100%', textAlign: 'center', boxShadow: '0 8px 40px rgba(0,0,0,0.08)' }}>
          <div style={{ width: 72, height: 72, background: '#FFFBEB', borderRadius: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
            <Clock size={36} color="#F59E0B" />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 12 }}>Account Pending Approval</h2>
          <div style={{ background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 10, padding: '16px 20px', marginBottom: 24 }}>
            <p style={{ fontSize: 13, color: '#78350F', lineHeight: 1.6 }}>
              Your supplier account has been submitted and is currently under review by our administrator team. You will receive an email notification once your account is approved. This typically takes <strong>1–2 business days</strong>.
            </p>
          </div>
          <p style={{ fontSize: 13, color: '#6B7280', marginBottom: 28 }}>
            Logged in as: <strong>{supplierUser.email}</strong>
          </p>
          <Link
            to="/supplier/login"
            onClick={async () => { await supabase.auth.signOut(); }}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: '#F3F4F6', color: '#374151', borderRadius: 10, padding: '10px 24px', fontSize: 14, fontWeight: 600, textDecoration: 'none' }}
          >
            Sign Out
          </Link>
        </div>
      </div>
    );
  }

  return <Outlet />;
}
