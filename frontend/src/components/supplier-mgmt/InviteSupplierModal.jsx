/**
 * InviteSupplierModal.jsx — Professional modal for sending supplier invitations.
 */

import { useState } from 'react';
import { X, Send, Building2, Mail, User, Phone, Globe, Tag, Package, Star, AlertCircle, CheckCircle2, Loader } from 'lucide-react';
import { sendInvitation } from '../../services/supplierManagementApi';

const CATEGORIES = [
  'Electronics & Semiconductors', 'Automotive Parts', 'Aerospace & Defence',
  'Pharmaceutical', 'Chemical', 'FMCG / Consumer Goods',
  'Industrial Machinery', 'Packaging', 'Raw Materials', 'Logistics', 'Other',
];
const RELATIONSHIPS = ['Strategic', 'Preferred', 'Standard', 'Backup', 'Spot'];

const INIT = {
  supplier_email: '', supplier_company_name: '', contact_name: '', phone: '',
  country: '', business_category: '', components_expected: '',
  relationship_type: 'Standard', is_critical: false, invitation_message: '', expiry_days: 7,
};

function Field({ label, icon: Icon, error, required, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'flex', alignItems: 'center', gap: 5 }}>
        {Icon && <Icon size={12} color="#6B7280" />}
        {label}
        {required && <span style={{ color: '#EF4444', marginLeft: 2 }}>*</span>}
      </label>
      {children}
      {error && <p style={{ fontSize: 11, color: '#EF4444', margin: 0 }}>{error}</p>}
    </div>
  );
}

function inp(hasErr) {
  return {
    width: '100%', border: `1px solid ${hasErr ? '#FCA5A5' : '#E5E7EB'}`,
    borderRadius: 8, padding: '9px 12px', fontSize: 13, outline: 'none',
    boxSizing: 'border-box', background: 'white', color: '#111827',
    transition: 'border 0.15s',
  };
}

export default function InviteSupplierModal({ onClose, onSuccess }) {
  const [form, setForm] = useState(INIT);
  const [errors, setErrors] = useState({});
  const [state, setState] = useState('idle'); // idle | loading | success | error
  const [serverError, setServerError] = useState('');
  const [createdToken, setCreatedToken] = useState('');

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  function validate() {
    const e = {};
    if (!form.supplier_email) e.supplier_email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(form.supplier_email)) e.supplier_email = 'Invalid email';
    if (!form.supplier_company_name) e.supplier_company_name = 'Company name is required';
    if (!form.contact_name) e.contact_name = 'Contact name is required';
    return e;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setState('loading');
    try {
      const result = await sendInvitation(form);
      setCreatedToken(result.token || '');
      setState('success');
      onSuccess?.();
    } catch (err) {
      setServerError(err.message);
      setState('error');
    }
  }

  const registrationUrl = createdToken
    ? `${window.location.origin}/supplier/register?token=${createdToken}`
    : '';

  if (state === 'success') {
    return (
      <div style={overlayStyle}>
        <div style={{ ...modalStyle, maxWidth: 480, textAlign: 'center', padding: '48px 40px' }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%',
            background: 'linear-gradient(135deg, #D1FAE5, #A7F3D0)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 20px', border: '3px solid #6EE7B7',
          }}>
            <CheckCircle2 size={30} color="#10B981" />
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 800, color: '#111827', marginBottom: 8 }}>Invitation Sent!</h2>
          <p style={{ fontSize: 13, color: '#6B7280', marginBottom: 20 }}>
            An invitation has been sent to <strong>{form.supplier_email}</strong>.
            You can also share this registration link directly:
          </p>
          <div style={{
            background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 8,
            padding: '10px 14px', fontSize: 12, color: '#374151',
            wordBreak: 'break-all', textAlign: 'left', marginBottom: 24,
            fontFamily: 'monospace',
          }}>
            {registrationUrl || `${window.location.origin}/supplier/register?token=...`}
          </div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
            {registrationUrl && (
              <button onClick={() => { navigator.clipboard.writeText(registrationUrl); }}
                style={secondaryBtn}>📋 Copy Link</button>
            )}
            <button onClick={onClose} style={primaryBtn}>Done</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={overlayStyle} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={modalStyle}>
        {/* Header */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '20px 24px', borderBottom: '1px solid #F3F4F6',
        }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 800, color: '#111827', margin: 0 }}>Invite Supplier</h2>
            <p style={{ fontSize: 12, color: '#6B7280', margin: '2px 0 0' }}>
              Send a secure invitation link to a new supplier
            </p>
          </div>
          <button onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 4 }}>
            <X size={18} color="#6B7280" />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '20px 24px', overflowY: 'auto', maxHeight: '70vh' }}>
          {state === 'error' && (
            <div style={{
              display: 'flex', gap: 10, alignItems: 'flex-start',
              background: '#FEF2F2', border: '1px solid #FECACA',
              borderRadius: 8, padding: '10px 14px', marginBottom: 16,
            }}>
              <AlertCircle size={15} color="#EF4444" style={{ flexShrink: 0, marginTop: 1 }} />
              <span style={{ fontSize: 13, color: '#DC2626' }}>{serverError}</span>
            </div>
          )}

          {/* Section: Recipient */}
          <SectionTitle>Supplier Details</SectionTitle>
          <div style={grid2}>
            <Field label="Supplier Company Name" icon={Building2} error={errors.supplier_company_name} required>
              <input style={inp(errors.supplier_company_name)} value={form.supplier_company_name}
                onChange={e => set('supplier_company_name', e.target.value)} placeholder="Acme Electronics Pvt. Ltd." />
            </Field>
            <Field label="Business Email" icon={Mail} error={errors.supplier_email} required>
              <input style={inp(errors.supplier_email)} type="email" value={form.supplier_email}
                onChange={e => set('supplier_email', e.target.value)} placeholder="contact@acme.com" />
            </Field>
            <Field label="Primary Contact Name" icon={User} error={errors.contact_name} required>
              <input style={inp(errors.contact_name)} value={form.contact_name}
                onChange={e => set('contact_name', e.target.value)} placeholder="John Smith" />
            </Field>
            <Field label="Phone Number" icon={Phone}>
              <input style={inp()} value={form.phone}
                onChange={e => set('phone', e.target.value)} placeholder="+91 98765 43210" />
            </Field>
            <Field label="Country" icon={Globe}>
              <input style={inp()} value={form.country}
                onChange={e => set('country', e.target.value)} placeholder="India" />
            </Field>
            <Field label="Business Category" icon={Tag}>
              <select style={inp()} value={form.business_category}
                onChange={e => set('business_category', e.target.value)}>
                <option value="">Select category…</option>
                {CATEGORIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </Field>
          </div>

          {/* Section: Relationship */}
          <SectionTitle>Relationship & Scope</SectionTitle>
          <div style={grid2}>
            <Field label="Relationship Type" icon={Star}>
              <select style={inp()} value={form.relationship_type}
                onChange={e => set('relationship_type', e.target.value)}>
                {RELATIONSHIPS.map(r => <option key={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="Invitation Expiry (days)">
              <input style={inp()} type="number" min="1" max="90" value={form.expiry_days}
                onChange={e => set('expiry_days', parseInt(e.target.value) || 7)} />
            </Field>
          </div>
          <Field label="Components Expected" icon={Package}>
            <input style={inp()} value={form.components_expected}
              onChange={e => set('components_expected', e.target.value)}
              placeholder="OLED panels, CPUs, Li-Ion batteries…" />
          </Field>

          {/* Critical toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 14, marginBottom: 14 }}>
            <div
              onClick={() => set('is_critical', !form.is_critical)}
              style={{
                width: 40, height: 22, borderRadius: 11, cursor: 'pointer',
                background: form.is_critical ? '#EF4444' : '#E5E7EB',
                position: 'relative', transition: 'background 0.2s', flexShrink: 0,
              }}
            >
              <div style={{
                position: 'absolute', top: 2, left: form.is_critical ? 20 : 2,
                width: 18, height: 18, borderRadius: '50%', background: 'white',
                transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
              }} />
            </div>
            <span style={{ fontSize: 13, fontWeight: 600, color: form.is_critical ? '#EF4444' : '#374151' }}>
              Critical Supplier (single-source / high dependency)
            </span>
          </div>

          {/* Message */}
          <Field label="Invitation Message (optional)">
            <textarea style={{ ...inp(), resize: 'vertical', minHeight: 80 }}
              value={form.invitation_message} rows={3}
              onChange={e => set('invitation_message', e.target.value)}
              placeholder="Welcome to our supplier network! We look forward to building a strong partnership…" />
          </Field>
        </form>

        {/* Footer */}
        <div style={{
          display: 'flex', justifyContent: 'flex-end', gap: 10,
          padding: '16px 24px', borderTop: '1px solid #F3F4F6',
        }}>
          <button onClick={onClose} style={secondaryBtn} type="button">Cancel</button>
          <button onClick={handleSubmit} style={primaryBtn} disabled={state === 'loading'} type="button">
            {state === 'loading'
              ? <><Loader size={13} style={{ animation: 'spin 1s linear infinite' }} /> Sending…</>
              : <><Send size={13} /> Send Invitation</>}
          </button>
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <div style={{
      fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase',
      letterSpacing: '0.05em', marginBottom: 12, marginTop: 18, paddingBottom: 6,
      borderBottom: '1px solid #F3F4F6',
    }}>{children}</div>
  );
}

const overlayStyle = {
  position: 'fixed', inset: 0, background: 'rgba(17,24,39,0.5)',
  display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
  backdropFilter: 'blur(4px)',
};
const modalStyle = {
  background: 'white', borderRadius: 16, width: '100%', maxWidth: 680,
  boxShadow: '0 25px 50px rgba(0,0,0,0.25)', margin: 16,
};
const primaryBtn = {
  display: 'inline-flex', alignItems: 'center', gap: 6,
  padding: '9px 20px', borderRadius: 8, border: 'none',
  background: 'linear-gradient(135deg, #2563EB, #1D4ED8)',
  color: 'white', fontSize: 13, fontWeight: 700, cursor: 'pointer',
};
const secondaryBtn = {
  padding: '9px 16px', borderRadius: 8, border: '1px solid #E5E7EB',
  background: 'white', color: '#374151', fontSize: 13, fontWeight: 600, cursor: 'pointer',
};
const grid2 = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 };
