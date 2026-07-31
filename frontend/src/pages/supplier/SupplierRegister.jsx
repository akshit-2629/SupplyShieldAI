import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff, ShieldCheck, Loader, AlertCircle, CheckCircle2, ArrowLeft, Building2, Globe, Phone, Mail, User, Lock, Briefcase, Tag } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { validateInvitationToken } from '../../services/supplierManagementApi';

const COUNTRIES = ['United States','United Kingdom','Canada','Germany','France','Japan','China','India','Australia','Singapore','Netherlands','Sweden','South Korea','Brazil','Mexico','Other'];
const INDUSTRIES = ['Automotive','Aerospace & Defense','Electronics & Semiconductors','Food & Beverage','Pharmaceuticals','Chemicals','Textiles & Apparel','Industrial Machinery','Consumer Goods','Logistics & Transportation','Construction Materials','Energy & Utilities','Healthcare Equipment','Agriculture','Other'];

function PasswordStrength({ password }) {
  const checks = [
    { label: 'At least 8 characters', ok: password.length >= 8 },
    { label: 'Uppercase letter', ok: /[A-Z]/.test(password) },
    { label: 'Number', ok: /\d/.test(password) },
    { label: 'Special character', ok: /[^A-Za-z0-9]/.test(password) },
  ];
  const score = checks.filter((c) => c.ok).length;
  const colors = ['#EF4444', '#F59E0B', '#F59E0B', '#10B981', '#10B981'];
  const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];

  if (!password) return null;
  return (
    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
        {[0,1,2,3].map((i) => (
          <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: i < score ? colors[score] : '#E5E7EB', transition: 'background 0.3s' }} />
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontSize: 11, color: colors[score], fontWeight: 600 }}>{labels[score]}</span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {checks.map((c) => (
          <div key={c.label} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: c.ok ? '#10B981' : '#9CA3AF' }}>
            <CheckCircle2 size={11} />
            {c.label}
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function Field({ label, icon: Icon, error, children }) {
  return (
    <div>
      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'flex', alignItems: 'center', gap: 5, marginBottom: 6 }}>
        {Icon && <Icon size={13} color="#6B7280" />}
        {label}
      </label>
      {children}
      {error && <p style={{ fontSize: 11, color: '#EF4444', marginTop: 4 }}>{error}</p>}
    </div>
  );
}

function inputStyle(hasError) {
  return {
    width: '100%', border: `1px solid ${hasError ? '#FCA5A5' : '#E5E7EB'}`, borderRadius: 8,
    padding: '10px 14px', fontSize: 13.5, outline: 'none', transition: 'border 0.15s', boxSizing: 'border-box',
    background: 'white',
  };
}

export default function SupplierRegister() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const inviteToken = searchParams.get('token') || '';

  const [step, setStep] = useState(1); // 1 = form, 2 = success
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  // ── Invitation state ──
  const [inviteLoading, setInviteLoading] = useState(!!inviteToken);
  const [inviteData, setInviteData]       = useState(null);   // validated invitation info
  const [inviteError, setInviteError]     = useState('');     // invalid / expired

  // On mount: validate invitation token if present, or show wall immediately
  useEffect(() => {
    if (!inviteToken) {
      // No token — show the 'Invitation Required' wall immediately
      setInviteError('Supplier registration is by invitation only. Please use the invitation link sent to your email by the manufacturer.');
      return;
    }

    setInviteLoading(true);
    validateInvitationToken(inviteToken)
      .then(res => {
        if (res.valid) {
          setInviteData(res);
          // Pre-fill form with invitation data
          setForm(f => ({
            ...f,
            email:       res.supplier_email  || f.email,
            companyName: res.supplier_company_name || f.companyName,
            contactName: res.contact_name    || f.contactName,
            industry:    res.business_category || f.industry,
          }));
        } else {
          setInviteError(res.error || 'This invitation link is invalid or has expired.');
        }
      })
      .catch(() => setInviteError('Could not validate invitation. Please try again.'))
      .finally(() => setInviteLoading(false));
  }, [inviteToken]);

  const [form, setForm] = useState({
    companyName: '', legalName: '', contactName: '',
    email: '', phone: '', country: '', industry: '',
    website: '', password: '', confirmPassword: '', acceptTerms: false,
  });
  const [errors, setErrors] = useState({});

  const set = (field) => (e) => setForm((p) => ({ ...p, [field]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  function validate() {
    const e = {};
    if (!form.companyName.trim()) e.companyName = 'Required';
    if (!form.legalName.trim()) e.legalName = 'Required';
    if (!form.contactName.trim()) e.contactName = 'Required';
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) e.email = 'Valid email required';
    if (!form.phone.trim()) e.phone = 'Required';
    if (!form.country) e.country = 'Select a country';
    if (!form.industry) e.industry = 'Select an industry';
    if (form.password.length < 8) e.password = 'At least 8 characters';
    if (form.password !== form.confirmPassword) e.confirmPassword = 'Passwords do not match';
    if (!form.acceptTerms) e.acceptTerms = 'You must accept the terms';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setApiError('');
    if (!validate()) return;

    // Invitation token is REQUIRED — self-registration is disabled.
    // SupplierRegister is only reachable via a manufacturer invitation link.
    if (!inviteToken || !inviteData?.valid) {
      setApiError('A valid invitation token is required to register as a supplier.');
      return;
    }

    const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/supplier-portal/auth/register`, {

        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email:            form.email,
          password:         form.password,
          company_name:     form.companyName,
          contact_name:     form.contactName,
          phone:            form.phone,
          invitation_token: inviteToken,
        }),
      });
      const data = await res.json();
      if (!res.ok) { setApiError(data.detail || data.message || 'Registration failed'); setLoading(false); return; }
      setStep(2);
    } catch (err) {
      setApiError(err.message);
    }
    setLoading(false);
  }

  if (step === 2) {
    return (
      <div style={{ minHeight: '100vh', background: '#F9FAFB', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 20, padding: '48px 40px', maxWidth: 480, width: '100%', textAlign: 'center', boxShadow: '0 8px 40px rgba(0,0,0,0.08)' }}>
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            style={{ width: 80, height: 80, background: '#ECFDF5', borderRadius: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
            <CheckCircle2 size={40} color="#10B981" />
          </motion.div>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: '#111827', marginBottom: 12 }}>Registration Submitted!</h2>
          <div style={{ background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 10, padding: '16px 20px', marginBottom: 24 }}>
            <p style={{ fontSize: 14, color: '#92400E', fontWeight: 600, marginBottom: 4 }}>⏳ Pending Administrator Approval</p>
            <p style={{ fontSize: 13, color: '#78350F', lineHeight: 1.6 }}>
              Your account has been created and is currently under review. You will receive an email at <strong>{form.email}</strong> once an administrator approves your account. This typically takes 1–2 business days.
            </p>
          </div>
          <p style={{ fontSize: 13, color: '#6B7280', marginBottom: 28, lineHeight: 1.6 }}>
            In the meantime, ensure your company information is accurate. You'll be able to complete your full profile after approval.
          </p>
          <Link to="/supplier/login" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'linear-gradient(135deg, #10B981, #059669)', color: 'white', borderRadius: 10, padding: '12px 28px', fontSize: 14, fontWeight: 700, textDecoration: 'none', boxShadow: '0 4px 14px rgba(16,185,129,0.3)' }}>
            Go to Sign In
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#F9FAFB', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '32px 20px' }}>
      <div style={{ width: '100%', maxWidth: 640 }}>

        {/* ── Invitation: validating ── */}
        {inviteLoading && (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <Loader size={28} color="#2563EB" style={{ animation: 'spin 1s linear infinite', marginBottom: 12 }} />
            <p style={{ fontSize: 14, color: '#6B7280' }}>Validating your invitation…</p>
          </div>
        )}

        {/* ── Invitation: invalid/expired ── */}
        {!inviteLoading && inviteError && (
          <div style={{
            background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 12,
            padding: '24px', textAlign: 'center', marginBottom: 24,
          }}>
            <AlertCircle size={32} color="#EF4444" style={{ marginBottom: 10 }} />
            <h2 style={{ fontSize: 16, fontWeight: 800, color: '#111827', marginBottom: 6 }}>Invitation Required</h2>
            <p style={{ fontSize: 13, color: '#6B7280', lineHeight: 1.7, marginBottom: 20 }}>
              {inviteError}
              <br />Supplier registration is by invitation only. Please contact your manufacturer partner to receive a valid invitation link.
            </p>
            <Link to="/supplier/login" style={{ fontSize: 13, color: '#2563EB', fontWeight: 700 }}>
              Already registered? Sign in →
            </Link>
          </div>
        )}

        {/* ── Only render form if no token error (or no token at all) ── */}
        {!inviteLoading && !inviteError && (
          <>
            {/* ── Invitation: valid — show info banner ── */}
            {inviteData && (
              <div style={{
                background: 'linear-gradient(135deg, #EFF6FF, #F5F3FF)',
                border: '1px solid #DBEAFE', borderRadius: 12,
                padding: '14px 18px', marginBottom: 20,
                display: 'flex', alignItems: 'center', gap: 12,
              }}>
                <CheckCircle2 size={20} color="#2563EB" style={{ flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#1E40AF' }}>
                    Invited by {inviteData.manufacturer_name}
                  </div>
                  <div style={{ fontSize: 12, color: '#6B7280', marginTop: 2 }}>
                    {inviteData.business_category && `Category: ${inviteData.business_category}`}
                    {inviteData.relationship_type ? ` · ${inviteData.relationship_type} supplier` : ''}
                    {inviteData.expires_at ? ` · Expires ${new Date(inviteData.expires_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}` : ''}
                  </div>
                </div>
              </div>
            )}

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 16 }}>
            <div style={{ width: 44, height: 44, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldCheck size={22} color="white" strokeWidth={2} />
            </div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: 20, padding: '4px 12px' }}>
              <Building2 size={13} color="#10B981" />
              <span style={{ fontSize: 12, fontWeight: 600, color: '#10B981' }}>Supplier Registration</span>
            </div>
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#111827', marginBottom: 8 }}>Create Supplier Account</h1>
          <p style={{ fontSize: 14, color: '#6B7280' }}>Join the SupplyShield AI partner network</p>
        </motion.div>

        {/* Form Card */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card" style={{ padding: '32px 36px' }}>
          {apiError && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, padding: '10px 14px', marginBottom: 20, fontSize: 13, color: '#DC2626' }}>
              <AlertCircle size={14} /> {apiError}
            </motion.div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Section: Company */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#10B981', textTransform: 'uppercase', marginBottom: 16, paddingBottom: 8, borderBottom: '1px solid #F3F4F6' }}>
                Company Information
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <Field label="Company Name" icon={Building2} error={errors.companyName}>
                  <input style={inputStyle(errors.companyName)} value={form.companyName} onChange={set('companyName')} placeholder="Acme Manufacturing" onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = errors.companyName ? '#FCA5A5' : '#E5E7EB'; }} />
                </Field>
                <Field label="Legal Business Name" icon={Briefcase} error={errors.legalName}>
                  <input style={inputStyle(errors.legalName)} value={form.legalName} onChange={set('legalName')} placeholder="Acme Manufacturing LLC" onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = errors.legalName ? '#FCA5A5' : '#E5E7EB'; }} />
                </Field>
              </div>
            </div>

            {/* Section: Contact */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#10B981', textTransform: 'uppercase', marginBottom: 16, paddingBottom: 8, borderBottom: '1px solid #F3F4F6' }}>
                Primary Contact
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <Field label="Contact Name" icon={User} error={errors.contactName}>
                  <input style={inputStyle(errors.contactName)} value={form.contactName} onChange={set('contactName')} placeholder="Jane Smith" onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = errors.contactName ? '#FCA5A5' : '#E5E7EB'; }} />
                </Field>
                <Field label="Official Business Email" icon={Mail} error={errors.email}>
                  <input type="email" style={inputStyle(errors.email)} value={form.email} onChange={set('email')} placeholder="jane@company.com" onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = errors.email ? '#FCA5A5' : '#E5E7EB'; }} />
                </Field>
                <Field label="Phone Number" icon={Phone} error={errors.phone}>
                  <input style={inputStyle(errors.phone)} value={form.phone} onChange={set('phone')} placeholder="+1 (555) 000-0000" onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = errors.phone ? '#FCA5A5' : '#E5E7EB'; }} />
                </Field>
                <Field label="Company Website (optional)" icon={Globe} error={errors.website}>
                  <input style={inputStyle(false)} value={form.website} onChange={set('website')} placeholder="https://company.com" onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; }} />
                </Field>
              </div>
            </div>

            {/* Section: Business Details */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#10B981', textTransform: 'uppercase', marginBottom: 16, paddingBottom: 8, borderBottom: '1px solid #F3F4F6' }}>
                Business Details
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <Field label="Country" icon={Globe} error={errors.country}>
                  <select style={{ ...inputStyle(errors.country), appearance: 'none', cursor: 'pointer' }} value={form.country} onChange={set('country')} onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = errors.country ? '#FCA5A5' : '#E5E7EB'; }}>
                    <option value="">Select country...</option>
                    {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </Field>
                <Field label="Industry" icon={Briefcase} error={errors.industry}>
                  <select style={{ ...inputStyle(errors.industry), appearance: 'none', cursor: 'pointer' }} value={form.industry} onChange={set('industry')} onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = errors.industry ? '#FCA5A5' : '#E5E7EB'; }}>
                    <option value="">Select industry...</option>
                    {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
                  </select>
                </Field>
              </div>
            </div>

            {/* Section: Security */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#10B981', textTransform: 'uppercase', marginBottom: 16, paddingBottom: 8, borderBottom: '1px solid #F3F4F6' }}>
                Account Security
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <Field label="Password" icon={Lock} error={errors.password}>
                  <div style={{ position: 'relative' }}>
                    <input type={showPass ? 'text' : 'password'} style={{ ...inputStyle(errors.password), paddingRight: 40 }} value={form.password} onChange={set('password')} placeholder="Create password" onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = errors.password ? '#FCA5A5' : '#E5E7EB'; }} />
                    <button type="button" onClick={() => setShowPass(!showPass)} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}>
                      {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                  <PasswordStrength password={form.password} />
                </Field>
                <Field label="Confirm Password" icon={Lock} error={errors.confirmPassword}>
                  <div style={{ position: 'relative' }}>
                    <input type={showConfirm ? 'text' : 'password'} style={{ ...inputStyle(errors.confirmPassword), paddingRight: 40 }} value={form.confirmPassword} onChange={set('confirmPassword')} placeholder="Confirm password" onFocus={(e) => { e.target.style.borderColor = '#10B981'; }} onBlur={(e) => { e.target.style.borderColor = errors.confirmPassword ? '#FCA5A5' : '#E5E7EB'; }} />
                    <button type="button" onClick={() => setShowConfirm(!showConfirm)} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}>
                      {showConfirm ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </Field>
              </div>
            </div>

            {/* Terms */}
            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer' }}>
                <input type="checkbox" checked={form.acceptTerms} onChange={set('acceptTerms')} style={{ marginTop: 2, accentColor: '#10B981', cursor: 'pointer', flexShrink: 0 }} />
                <span style={{ fontSize: 13, color: '#6B7280', lineHeight: 1.5 }}>
                  I agree to the <span style={{ color: '#10B981', fontWeight: 600, cursor: 'pointer' }}>Terms of Service</span> and <span style={{ color: '#10B981', fontWeight: 600, cursor: 'pointer' }}>Privacy Policy</span>. I understand my account will remain <strong>pending until approved</strong> by an administrator.
                </span>
              </label>
              {errors.acceptTerms && <p style={{ fontSize: 11, color: '#EF4444', marginTop: 4 }}>{errors.acceptTerms}</p>}
            </div>

            {/* Submit */}
            <motion.button type="submit" disabled={loading}
              whileHover={{ scale: loading ? 1 : 1.01 }} whileTap={{ scale: loading ? 1 : 0.99 }}
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, background: loading ? '#9CA3AF' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', border: 'none', borderRadius: 10, padding: '13px 16px', fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', boxShadow: loading ? 'none' : '0 4px 16px rgba(16,185,129,0.3)', transition: 'all 0.2s' }}>
              {loading ? <><Loader size={16} className="animate-spin-slow" /> Creating account...</> : 'Create Supplier Account'}
            </motion.button>
          </form>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} style={{ textAlign: 'center', marginTop: 20 }}>
          <p style={{ fontSize: 13, color: '#9CA3AF', marginBottom: 10 }}>
            Already have an account?{' '}
            <Link to="/supplier/login" style={{ color: '#10B981', fontWeight: 600 }}>Sign In</Link>
          </p>
          <Link to="/role-select" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#6B7280', fontWeight: 500 }}>
            <ArrowLeft size={14} /> Back to Role Selection
          </Link>
        </motion.div>
        </>
        )}
      </div>
    </div>
  );
}
