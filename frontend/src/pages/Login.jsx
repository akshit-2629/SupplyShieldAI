import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff, ShieldCheck, Loader, AlertCircle, ArrowRight, BarChart3, Clock } from 'lucide-react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../context/AuthContext';
import { getSetupStatus } from '../services/manufacturerApi';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, loading: authLoading } = useAuth();
  const [email,         setEmail]         = useState('');
  const [password,      setPassword]      = useState('');
  const [showPass,      setShowPass]      = useState(false);
  const [loading,       setLoading]       = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const sessionExpired = searchParams.get('error') === 'session_expired';
  const [error, setError] = useState(
    sessionExpired ? 'Your session has expired. Please sign in again.' : ''
  );


  // Already authenticated → send to dashboard
  useEffect(() => {
    if (!authLoading && user) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, authLoading, navigate]);

  async function handleLogin(e) {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('Please enter your email and password.');
      return;
    }
    setLoading(true);
    const { data, error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    if (signInError) {
      setLoading(false);
      setError(signInError.message);
      return;
    }
    // Block suppliers from logging in via manufacturer portal
    const role = data?.user?.user_metadata?.role;
    if (role === 'supplier') {
      await supabase.auth.signOut();
      setLoading(false);
      setError('This account is registered as a supplier. Please use the Supplier Login.');
      return;
    }
    // Check if manufacturer setup is complete
    try {
      const status = await getSetupStatus();
      setLoading(false);
      navigate(status?.complete ? '/dashboard' : '/setup', { replace: true });
    } catch {
      setLoading(false);
      navigate('/setup', { replace: true }); // Default to setup on error
    }
  }

  async function handleGoogleLogin() {
    setError('');
    setGoogleLoading(true);
    const { error: oauthError } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    if (oauthError) {
      setError(oauthError.message);
      setGoogleLoading(false);
    }
    // On success, browser redirects to Google — no further code needed here
  }

  return (
    <div style={{ minHeight: '100vh', background: '#F9FAFB', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      {/* Background decoration */}
      <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        <div style={{ position: 'absolute', top: -100, right: -100, width: 400, height: 400, background: 'radial-gradient(circle, rgba(37,99,235,0.06) 0%, transparent 70%)', borderRadius: '50%' }} />
        <div style={{ position: 'absolute', bottom: -100, left: -100, width: 400, height: 400, background: 'radial-gradient(circle, rgba(124,58,237,0.05) 0%, transparent 70%)', borderRadius: '50%' }} />
      </div>

      <div style={{ width: '100%', maxWidth: 440, position: 'relative' }}>
        {/* Logo */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
          style={{ textAlign: 'center', marginBottom: 32 }}
        >
          <div style={{ width: 56, height: 56, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }} className="animate-float">
            <ShieldCheck size={28} color="white" strokeWidth={2} />
          </div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 20, padding: '4px 12px', marginBottom: 12 }}>
            <BarChart3 size={13} color="#2563EB" />
            <span style={{ fontSize: 12, fontWeight: 600, color: '#2563EB' }}>Manufacturer Portal</span>
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: '#111827', marginBottom: 6 }}>Welcome back</h1>
          <p style={{ fontSize: 14, color: '#9CA3AF' }}>Sign in to your manufacturer workspace</p>
        </motion.div>

        {/* Card */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.1 }}
          className="card" style={{ padding: 32 }}
        >
          {/* Google SSO */}
          <button
            onClick={handleGoogleLogin}
            disabled={googleLoading || loading}
            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, background: 'white', border: '1px solid #E5E7EB', borderRadius: 10, padding: '11px 16px', fontSize: 14, fontWeight: 500, color: '#374151', cursor: googleLoading ? 'wait' : 'pointer', marginBottom: 20, transition: 'all 0.15s', opacity: googleLoading ? 0.7 : 1 }}
            onMouseEnter={e => { if (!googleLoading) e.currentTarget.style.background = '#F9FAFB'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'white'; }}
          >
            {googleLoading ? (
              <Loader size={16} style={{ animation: 'spin-slow 1.2s linear infinite' }} />
            ) : (
              <svg width="18" height="18" viewBox="0 0 48 48">
                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.29-8.16 2.29-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
              </svg>
            )}
            {googleLoading ? 'Redirecting to Google...' : 'Continue with Google'}
          </button>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <div style={{ flex: 1, height: 1, background: '#F3F4F6' }} />
            <span style={{ fontSize: 12, color: '#9CA3AF', fontWeight: 500 }}>or continue with email</span>
            <div style={{ flex: 1, height: 1, background: '#F3F4F6' }} />
          </div>

          {/* Error / Session Expired Banner */}
          {error && (
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: sessionExpired ? '#FFFBEB' : '#FEF2F2',
                border: `1px solid ${sessionExpired ? '#FDE68A' : '#FCA5A5'}`,
                borderRadius: 8, padding: '10px 14px', marginBottom: 16,
                fontSize: 13,
                color: sessionExpired ? '#92400E' : '#DC2626',
              }}>
              {sessionExpired
                ? <Clock size={14} />
                : <AlertCircle size={14} />}
              {' '}{error}
            </motion.div>
          )}

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>Email Address</label>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                placeholder="you@company.com" autoComplete="email"
                style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 8, padding: '10px 14px', fontSize: 14, outline: 'none', transition: 'border 0.15s' }}
                onFocus={e => e.target.style.borderColor = '#2563EB'}
                onBlur={e => e.target.style.borderColor = '#E5E7EB'}
              />
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Password</label>
                <button
                  type="button"
                  onClick={async () => {
                    if (!email) { setError('Enter your email first to reset your password.'); return; }
                    setError('');
                    const { error: resetErr } = await supabase.auth.resetPasswordForEmail(email, {
                      redirectTo: `${window.location.origin}/auth/callback`,
                    });
                    if (resetErr) setError(resetErr.message);
                    else setError('Password reset email sent! Check your inbox.');
                  }}
                  style={{ fontSize: 12, color: '#2563EB', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}
                >
                  Forgot password?
                </button>
              </div>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPass ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••" autoComplete="current-password"
                  style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 8, padding: '10px 40px 10px 14px', fontSize: 14, outline: 'none', transition: 'border 0.15s' }}
                  onFocus={e => e.target.style.borderColor = '#2563EB'}
                  onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}>
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <motion.button type="submit" disabled={loading || googleLoading}
              whileHover={{ scale: loading ? 1 : 1.01 }} whileTap={{ scale: loading ? 1 : 0.99 }}
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, background: loading ? '#9CA3AF' : 'linear-gradient(135deg, #2563EB, #7C3AED)', color: 'white', border: 'none', borderRadius: 10, padding: '12px 16px', fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', boxShadow: loading ? 'none' : '0 4px 14px rgba(37,99,235,0.3)', transition: 'all 0.2s', marginTop: 4 }}>
              {loading ? <><Loader size={16} className="animate-spin-slow" /> Signing in...</> : <>Sign In <ArrowRight size={16} /></>}
            </motion.button>
          </form>
        </motion.div>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}
          style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: '#9CA3AF' }}>
          Don't have an account?{' '}
          <Link to="/signup" style={{ color: '#2563EB', fontWeight: 600 }}>Register as Manufacturer</Link>
        </motion.p>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.45 }}
          style={{ textAlign: 'center', marginTop: 10, fontSize: 13, color: '#9CA3AF' }}>
          Are you a supplier?{' '}
          <Link to="/supplier/login" style={{ color: '#10B981', fontWeight: 600 }}>Supplier Login →</Link>
        </motion.p>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
          style={{ textAlign: 'center', marginTop: 10, fontSize: 13, color: '#9CA3AF' }}>
          <Link to="/role-select" style={{ color: '#9CA3AF' }}>← Back to Role Selection</Link>
        </motion.p>
      </div>
    </div>
  );
}
