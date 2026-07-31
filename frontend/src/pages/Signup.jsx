import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, ShieldCheck, Loader, AlertCircle, CheckCircle, ArrowRight, Info, BarChart3 } from 'lucide-react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../context/AuthContext';

function PasswordStrength({ password }) {
  const checks = [
    { label: 'At least 8 characters', pass: password.length >= 8 },
    { label: 'Contains uppercase letter', pass: /[A-Z]/.test(password) },
    { label: 'Contains a number', pass: /\d/.test(password) },
  ];
  const score = checks.filter(c => c.pass).length;
  const colors = ['#E5E7EB', '#DC2626', '#D97706', '#059669'];
  const labels = ['', 'Weak', 'Fair', 'Strong'];

  if (!password) return null;
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
        {[1, 2, 3].map(i => (
          <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: i <= score ? colors[score] : '#E5E7EB', transition: 'background 0.3s' }} />
        ))}
      </div>
      <div style={{ fontSize: 11, color: colors[score], fontWeight: 600, marginBottom: 6 }}>{labels[score]}</div>
      {checks.map(c => (
        <div key={c.label} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: c.pass ? '#059669' : '#9CA3AF', marginBottom: 2 }}>
          <CheckCircle size={10} color={c.pass ? '#059669' : '#D1D5DB'} />
          {c.label}
        </div>
      ))}
    </div>
  );
}

export default function Signup() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [agreed, setAgreed] = useState(false);

  // Already authenticated → send to dashboard
  useEffect(() => {
    if (!authLoading && user) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, authLoading, navigate]);

  async function handleSignup(e) {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!fullName.trim()) { setError('Please enter your full name.'); return; }
    if (!email) { setError('Please enter your email address.'); return; }
    if (password.length < 8) { setError('Password must be at least 8 characters.'); return; }
    if (password !== confirmPassword) { setError('Passwords do not match.'); return; }
    if (!agreed) { setError('Please agree to the Terms of Service to continue.'); return; }

    setLoading(true);
    const { error: signUpError, data } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName },
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    setLoading(false);

    if (signUpError) {
      setError(signUpError.message);
      return;
    }

    // Supabase may auto-confirm or require email confirmation depending on project settings
    if (data.user && data.session) {
      // Email confirmations disabled — user is immediately signed in
      // New manufacturers always go to /setup wizard first
      navigate('/setup', { replace: true });
    } else {
      setSuccess('Account created! Check your email to confirm your address, then sign in.');
    }
  }

  async function handleGoogleSignup() {
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
  }

  return (
    <div style={{ minHeight: '100vh', background: '#F9FAFB', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '32px 20px' }}>
      {/* Background decoration */}
      <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        <div style={{ position: 'absolute', top: -80, right: -80, width: 360, height: 360, background: 'radial-gradient(circle, rgba(124,58,237,0.06) 0%, transparent 70%)', borderRadius: '50%' }} />
        <div style={{ position: 'absolute', bottom: -80, left: -80, width: 360, height: 360, background: 'radial-gradient(circle, rgba(37,99,235,0.05) 0%, transparent 70%)', borderRadius: '50%' }} />
      </div>

      <div style={{ width: '100%', maxWidth: 460, position: 'relative' }}>
        {/* Logo */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
          style={{ textAlign: 'center', marginBottom: 28 }}
        >
          <div style={{ width: 56, height: 56, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }} className="animate-float">
            <ShieldCheck size={28} color="white" strokeWidth={2} />
          </div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 20, padding: '4px 12px', marginBottom: 12 }}>
            <BarChart3 size={13} color="#2563EB" />
            <span style={{ fontSize: 12, fontWeight: 600, color: '#2563EB' }}>Manufacturer Registration</span>
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: '#111827', marginBottom: 6 }}>Create your manufacturer account</h1>
          <p style={{ fontSize: 14, color: '#9CA3AF' }}>Set up SupplyShield AI for your organisation</p>
        </motion.div>

        {/* Card */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.1 }}
          className="card" style={{ padding: 32 }}
        >
          {/* Google OAuth */}
          <button
            onClick={handleGoogleSignup}
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
            {googleLoading ? 'Redirecting to Google...' : 'Sign up with Google'}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <div style={{ flex: 1, height: 1, background: '#F3F4F6' }} />
            <span style={{ fontSize: 12, color: '#9CA3AF', fontWeight: 500 }}>or sign up with email</span>
            <div style={{ flex: 1, height: 1, background: '#F3F4F6' }} />
          </div>

          {/* Error */}
          {error && (
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
              style={{ display: 'flex', alignItems: 'flex-start', gap: 8, background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: 13, color: '#DC2626' }}>
              <AlertCircle size={14} style={{ marginTop: 1, flexShrink: 0 }} /> {error}
            </motion.div>
          )}

          {/* Success */}
          {success && (
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
              style={{ display: 'flex', alignItems: 'flex-start', gap: 8, background: '#D1FAE5', border: '1px solid #6EE7B7', borderRadius: 8, padding: '12px 14px', marginBottom: 16, fontSize: 13, color: '#065F46' }}>
              <CheckCircle size={14} style={{ marginTop: 1, flexShrink: 0 }} />
              <div>
                <div style={{ fontWeight: 600, marginBottom: 2 }}>Check your email</div>
                {success}
              </div>
            </motion.div>
          )}

          <form onSubmit={handleSignup} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Full Name */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>Full Name</label>
              <input
                type="text" value={fullName} onChange={e => setFullName(e.target.value)}
                placeholder="Akshit Kumar" autoComplete="name"
                style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 8, padding: '10px 14px', fontSize: 14, outline: 'none', transition: 'border 0.15s' }}
                onFocus={e => e.target.style.borderColor = '#2563EB'}
                onBlur={e => e.target.style.borderColor = '#E5E7EB'}
              />
            </div>

            {/* Email */}
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

            {/* Password */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPass ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="Min. 8 characters" autoComplete="new-password"
                  style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 8, padding: '10px 40px 10px 14px', fontSize: 14, outline: 'none', transition: 'border 0.15s' }}
                  onFocus={e => e.target.style.borderColor = '#2563EB'}
                  onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}>
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <PasswordStrength password={password} />
            </div>

            {/* Confirm Password */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>Confirm Password</label>
              <input
                type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
                placeholder="••••••••" autoComplete="new-password"
                style={{ width: '100%', border: `1px solid ${confirmPassword && confirmPassword !== password ? '#FCA5A5' : '#E5E7EB'}`, borderRadius: 8, padding: '10px 14px', fontSize: 14, outline: 'none', transition: 'border 0.15s' }}
                onFocus={e => e.target.style.borderColor = confirmPassword !== password ? '#FCA5A5' : '#2563EB'}
                onBlur={e => e.target.style.borderColor = confirmPassword && confirmPassword !== password ? '#FCA5A5' : '#E5E7EB'}
              />
              {confirmPassword && confirmPassword !== password && (
                <div style={{ fontSize: 11, color: '#DC2626', marginTop: 4 }}>Passwords do not match</div>
              )}
            </div>

            {/* Terms */}
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <input type="checkbox" id="terms" checked={agreed} onChange={e => setAgreed(e.target.checked)} style={{ width: 16, height: 16, cursor: 'pointer', marginTop: 2, flexShrink: 0 }} />
              <label htmlFor="terms" style={{ fontSize: 13, color: '#6B7280', cursor: 'pointer', lineHeight: 1.4 }}>
                I agree to the{' '}
                <span style={{ color: '#2563EB', fontWeight: 600 }}>Terms of Service</span>
                {' '}and{' '}
                <span style={{ color: '#2563EB', fontWeight: 600 }}>Privacy Policy</span>
              </label>
            </div>

            <motion.button type="submit" disabled={loading || googleLoading}
              whileHover={{ scale: loading ? 1 : 1.01 }} whileTap={{ scale: loading ? 1 : 0.99 }}
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, background: loading ? '#9CA3AF' : 'linear-gradient(135deg, #2563EB, #7C3AED)', color: 'white', border: 'none', borderRadius: 10, padding: '12px 16px', fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', boxShadow: loading ? 'none' : '0 4px 14px rgba(37,99,235,0.3)', transition: 'all 0.2s', marginTop: 4 }}>
              {loading ? <><Loader size={16} className="animate-spin-slow" /> Creating account...</> : <>Create Account <ArrowRight size={16} /></>}
            </motion.button>
          </form>

          {/* Email confirmation notice */}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 7, background: '#F0F9FF', border: '1px solid #BAE6FD', borderRadius: 8, padding: '10px 12px', marginTop: 16 }}>
            <Info size={13} color="#0369A1" style={{ marginTop: 1, flexShrink: 0 }} />
            <span style={{ fontSize: 12, color: '#0369A1', lineHeight: 1.5 }}>
              You may need to verify your email before accessing the dashboard.
            </span>
          </div>
        </motion.div>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}
          style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: '#9CA3AF' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: '#2563EB', fontWeight: 600 }}>Sign in</Link>
        </motion.p>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.45 }}
          style={{ textAlign: 'center', marginTop: 10, fontSize: 13, color: '#9CA3AF' }}>
          <Link to="/role-select" style={{ color: '#9CA3AF' }}>← Back to Role Selection</Link>
        </motion.p>
      </div>
    </div>
  );
}
