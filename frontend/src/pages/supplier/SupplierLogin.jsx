import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, ShieldCheck, Loader, AlertCircle, ArrowRight, Building2, ArrowLeft } from 'lucide-react';
import { supabase } from '../../lib/supabase';

export default function SupplierLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [forgotSent, setForgotSent] = useState(false);

  async function handleLogin(e) {
    e.preventDefault();
    setError('');
    if (!email || !password) { setError('Please enter your email and password.'); return; }
    setLoading(true);
    const { data, error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (signInError) { setError(signInError.message); return; }
    // Check supplier role in metadata
    const role = data?.user?.user_metadata?.role;
    if (role !== 'supplier') {
      await supabase.auth.signOut();
      setError('This account is not registered as a supplier. Please use the Admin login.');
      return;
    }
    navigate('/supplier/dashboard', { replace: true });
  }

  async function handleForgotPassword() {
    if (!email) { setError('Enter your email address first.'); return; }
    setError('');
    const { error: resetErr } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/supplier/login`,
    });
    if (resetErr) { setError(resetErr.message); return; }
    setForgotSent(true);
  }

  return (
    <div style={{ minHeight: '100vh', background: '#F9FAFB', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      {/* Background */}
      <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        <div style={{ position: 'absolute', top: -100, right: -100, width: 400, height: 400, background: 'radial-gradient(circle, rgba(16,185,129,0.07) 0%, transparent 70%)', borderRadius: '50%' }} />
        <div style={{ position: 'absolute', bottom: -100, left: -100, width: 400, height: 400, background: 'radial-gradient(circle, rgba(37,99,235,0.05) 0%, transparent 70%)', borderRadius: '50%' }} />
      </div>

      <div style={{ width: '100%', maxWidth: 440, position: 'relative' }}>
        {/* Logo */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 20 }}>
            <div className="animate-float" style={{ width: 48, height: 48, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldCheck size={24} color="white" strokeWidth={2} />
            </div>
          </div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: 20, padding: '4px 12px', marginBottom: 16 }}>
            <Building2 size={13} color="#10B981" />
            <span style={{ fontSize: 12, fontWeight: 600, color: '#10B981' }}>Supplier Portal</span>
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: '#111827', marginBottom: 6 }}>Supplier Sign In</h1>
          <p style={{ fontSize: 14, color: '#9CA3AF' }}>Access your supplier workspace</p>
        </motion.div>

        {/* Card */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.1 }} className="card" style={{ padding: 32 }}>
          {forgotSent ? (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} style={{ textAlign: 'center', padding: '16px 0' }}>
              <div style={{ width: 56, height: 56, background: '#ECFDF5', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                <ShieldCheck size={28} color="#10B981" />
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: '#111827', marginBottom: 8 }}>Check your inbox</h3>
              <p style={{ fontSize: 14, color: '#6B7280', marginBottom: 20 }}>We've sent a password reset link to <strong>{email}</strong></p>
              <button onClick={() => setForgotSent(false)} style={{ fontSize: 13, color: '#2563EB', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>← Back to login</button>
            </motion.div>
          ) : (
            <>
              {error && (
                <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: 13, color: '#DC2626' }}>
                  <AlertCircle size={14} /> {error}
                </motion.div>
              )}

              <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>Business Email</label>
                  <input
                    type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com" autoComplete="email"
                    style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 8, padding: '10px 14px', fontSize: 14, outline: 'none', transition: 'border 0.15s', boxSizing: 'border-box' }}
                    onFocus={(e) => { e.target.style.borderColor = '#10B981'; }}
                    onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Password</label>
                    <button type="button" onClick={handleForgotPassword}
                      style={{ fontSize: 12, color: '#10B981', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}>
                      Forgot password?
                    </button>
                  </div>
                  <div style={{ position: 'relative' }}>
                    <input
                      type={showPass ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••" autoComplete="current-password"
                      style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 8, padding: '10px 40px 10px 14px', fontSize: 14, outline: 'none', transition: 'border 0.15s', boxSizing: 'border-box' }}
                      onFocus={(e) => { e.target.style.borderColor = '#10B981'; }}
                      onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; }}
                    />
                    <button type="button" onClick={() => setShowPass(!showPass)}
                      style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}>
                      {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                {/* Remember me */}
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input
                    type="checkbox" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)}
                    style={{ width: 15, height: 15, accentColor: '#10B981', cursor: 'pointer' }}
                  />
                  <span style={{ fontSize: 13, color: '#6B7280' }}>Remember me for 30 days</span>
                </label>

                <motion.button type="submit" disabled={loading}
                  whileHover={{ scale: loading ? 1 : 1.01 }} whileTap={{ scale: loading ? 1 : 0.99 }}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, background: loading ? '#9CA3AF' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', border: 'none', borderRadius: 10, padding: '12px 16px', fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', boxShadow: loading ? 'none' : '0 4px 14px rgba(16,185,129,0.3)', transition: 'all 0.2s', marginTop: 4 }}>
                  {loading ? <><Loader size={16} className="animate-spin-slow" /> Signing in...</> : <>Sign In <ArrowRight size={16} /></>}
                </motion.button>
              </form>
            </>
          )}
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} style={{ textAlign: 'center', marginTop: 20 }}>
          <p style={{ fontSize: 13, color: '#9CA3AF', marginBottom: 10 }}>
            Don't have an account?{' '}
            <Link to="/supplier/register" style={{ color: '#10B981', fontWeight: 600 }}>Register as Supplier</Link>
          </p>
          <Link to="/role-select" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#6B7280', fontWeight: 500 }}>
            <ArrowLeft size={14} /> Back to Role Selection
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
