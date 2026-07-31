/**
 * Step1Company.jsx — Company Information form (Setup Wizard, Step 1).
 * Saves to POST /api/v1/manufacturer/company on "Continue".
 */

import { useState } from 'react';
import { Building2, Globe, Mail, Phone, Clock, Calendar, Loader, AlertCircle } from 'lucide-react';
import { useSetupStore } from '../../store/setupStore';
import { upsertCompany } from '../../services/manufacturerApi';

const INDUSTRIES = [
  'Electronics Manufacturing', 'Automotive', 'Aerospace & Defence',
  'Pharmaceutical', 'FMCG / Consumer Goods', 'Semiconductor',
  'Textile & Apparel', 'Heavy Machinery', 'Chemical', 'Food & Beverage', 'Other',
];

const COMPANY_SIZES = [
  { value: 'startup',     label: 'Startup  (1–50 employees)' },
  { value: 'sme',         label: 'SME  (51–250 employees)' },
  { value: 'mid_market',  label: 'Mid-Market  (251–1 000 employees)' },
  { value: 'enterprise',  label: 'Enterprise  (1 000+ employees)' },
];

const TIMEZONES = [
  'Asia/Kolkata', 'Asia/Singapore', 'Asia/Tokyo', 'Asia/Shanghai',
  'Europe/London', 'Europe/Berlin', 'America/New_York', 'America/Los_Angeles',
  'Australia/Sydney', 'UTC',
];

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function Field({ label, required, children, hint }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <label style={{ fontSize: 12, fontWeight: 700, color: '#374151', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label} {required && <span style={{ color: '#EF4444' }}>*</span>}
      </label>
      {children}
      {hint && <span style={{ fontSize: 11, color: '#9CA3AF' }}>{hint}</span>}
    </div>
  );
}

const inputStyle = {
  width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8,
  padding: '10px 12px', fontSize: 14, outline: 'none',
  background: 'white', color: '#111827', transition: 'border-color 0.15s',
  boxSizing: 'border-box',
};

function Input({ id, ...props }) {
  return (
    <input
      id={id}
      style={inputStyle}
      onFocus={(e) => (e.target.style.borderColor = '#2563EB')}
      onBlur={(e)  => (e.target.style.borderColor = '#E5E7EB')}
      {...props}
    />
  );
}

function Select({ id, children, ...props }) {
  return (
    <select
      id={id}
      style={{ ...inputStyle, cursor: 'pointer' }}
      onFocus={(e) => (e.target.style.borderColor = '#2563EB')}
      onBlur={(e)  => (e.target.style.borderColor = '#E5E7EB')}
      {...props}
    >
      {children}
    </select>
  );
}

export default function Step1Company({ onNext }) {
  const { company, updateCompany } = useSetupStore();
  const [saving, setSaving]  = useState(false);
  const [errors, setErrors]  = useState({});
  const [apiErr, setApiErr]  = useState('');

  const set = (k) => (e) => {
    updateCompany({ [k]: e.target.value });
    if (errors[k]) setErrors((prev) => ({ ...prev, [k]: '' }));
  };

  function validate() {
    const errs = {};
    if (!company.name.trim())    errs.name    = 'Company name is required';
    if (!company.country.trim()) errs.country = 'Country is required';
    if (!company.industry)       errs.industry = 'Industry is required';
    if (company.business_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(company.business_email)) {
      errs.business_email = 'Enter a valid email address';
    }
    return errs;
  }

  async function handleNext() {
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setApiErr('');
    setSaving(true);
    try {
      await upsertCompany({ ...company, onboarding_step: 2 });
      onNext();
    } catch (e) {
      setApiErr(e.message);
    } finally {
      setSaving(false);
    }
  }

  const toggleDay = (day) => {
    const days = company.working_days || [];
    updateCompany({
      working_days: days.includes(day) ? days.filter((d) => d !== day) : [...days, day],
    });
  };

  return (
    <div style={{ maxWidth: 720, animation: 'slideUp 0.3s ease both' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: '#EFF6FF', border: '1px solid #DBEAFE',
          borderRadius: 20, padding: '4px 12px', marginBottom: 12,
        }}>
          <Building2 size={13} color="#2563EB" />
          <span style={{ fontSize: 12, fontWeight: 600, color: '#2563EB' }}>Step 1 of 7</span>
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#111827', marginBottom: 6 }}>
          Company Information
        </h1>
        <p style={{ fontSize: 14, color: '#6B7280' }}>
          Tell us about your organisation. This becomes the foundation of your supply chain profile.
        </p>
      </div>

      {apiErr && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: '#FEF2F2', border: '1px solid #FECACA',
          borderRadius: 8, padding: '10px 14px', marginBottom: 20,
        }}>
          <AlertCircle size={14} color="#EF4444" />
          <span style={{ fontSize: 13, color: '#DC2626' }}>{apiErr}</span>
        </div>
      )}

      {/* ── Section: Core identity ── */}
      <Section icon={<Building2 size={15} color="#2563EB" />} title="Organisation Details">
        <Grid cols={2}>
          <Field label="Company Name" required>
            <Input id="company-name" value={company.name} onChange={set('name')}
              placeholder="Akshit Electronics Pvt. Ltd." />
            {errors.name && <Err>{errors.name}</Err>}
          </Field>

          <Field label="Industry" required>
            <Select id="industry" value={company.industry} onChange={set('industry')}>
              {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
            </Select>
            {errors.industry && <Err>{errors.industry}</Err>}
          </Field>
        </Grid>

        <Field label="Company Description"
          hint="Brief description of what your company manufactures.">
          <textarea
            value={company.description} onChange={(e) => updateCompany({ description: e.target.value })}
            rows={3} placeholder="We manufacture consumer electronics including smartphones, tablets and laptops..."
            style={{ ...inputStyle, resize: 'vertical', lineHeight: 1.5 }}
            onFocus={(e) => (e.target.style.borderColor = '#2563EB')}
            onBlur={(e)  => (e.target.style.borderColor = '#E5E7EB')}
          />
        </Field>

        <Grid cols={2}>
          <Field label="Company Size">
            <Select id="company-size" value={company.company_size} onChange={set('company_size')}>
              <option value="">Select size</option>
              {COMPANY_SIZES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </Select>
          </Field>
          <Field label="Annual Production Capacity" hint="e.g. 500,000 units/year">
            <Input id="annual-cap" value={company.annual_production_cap}
              onChange={set('annual_production_cap')} placeholder="500,000 units/year" />
          </Field>
        </Grid>
      </Section>

      {/* ── Section: Location ── */}
      <Section icon={<Globe size={15} color="#2563EB" />} title="Location">
        <Grid cols={3}>
          <Field label="Country" required>
            <Input id="country" value={company.country} onChange={set('country')}
              placeholder="India" />
            {errors.country && <Err>{errors.country}</Err>}
          </Field>
          <Field label="State / Province">
            <Input id="state" value={company.state} onChange={set('state')}
              placeholder="Karnataka" />
          </Field>
          <Field label="City">
            <Input id="city" value={company.city} onChange={set('city')}
              placeholder="Bengaluru" />
          </Field>
        </Grid>
        <Field label="Head Office Address">
          <Input id="address" value={company.address} onChange={set('address')}
            placeholder="123, Electronics City, Phase 1, Bengaluru 560 100" />
        </Field>
      </Section>

      {/* ── Section: Contact ── */}
      <Section icon={<Mail size={15} color="#2563EB" />} title="Contact & Web">
        <Grid cols={2}>
          <Field label="Website">
            <Input id="website" type="url" value={company.website} onChange={set('website')}
              placeholder="https://akshitelectronics.com" />
          </Field>
          <Field label="Business Email">
            <Input id="business-email" type="email" value={company.business_email}
              onChange={set('business_email')} placeholder="info@akshitelectronics.com" />
            {errors.business_email && <Err>{errors.business_email}</Err>}
          </Field>
          <Field label="Business Phone">
            <Input id="business-phone" type="tel" value={company.business_phone}
              onChange={set('business_phone')} placeholder="+91 98765 43210" />
          </Field>
          <Field label="Company Logo URL" hint="Paste a URL to your logo image">
            <Input id="logo-url" type="url" value={company.logo_url} onChange={set('logo_url')}
              placeholder="https://..." />
          </Field>
        </Grid>
      </Section>

      {/* ── Section: Legal ── */}
      <Section icon={<Building2 size={15} color="#2563EB" />} title="Legal">
        <Grid cols={2}>
          <Field label="Business Registration Number">
            <Input id="reg-no" value={company.registration_number}
              onChange={set('registration_number')} placeholder="U74999KA2024PTC123456" />
          </Field>
          <Field label="GST / Tax Number" hint="Optional">
            <Input id="tax-no" value={company.tax_number} onChange={set('tax_number')}
              placeholder="29AABCU9603R1ZV" />
          </Field>
        </Grid>
      </Section>

      {/* ── Section: Operations ── */}
      <Section icon={<Clock size={15} color="#2563EB" />} title="Operational Hours">
        <Grid cols={3}>
          <Field label="Timezone">
            <Select id="timezone" value={company.timezone} onChange={set('timezone')}>
              {TIMEZONES.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
            </Select>
          </Field>
          <Field label="Work Starts">
            <Input id="work-start" type="time" value={company.working_hours_start}
              onChange={set('working_hours_start')} />
          </Field>
          <Field label="Work Ends">
            <Input id="work-end" type="time" value={company.working_hours_end}
              onChange={set('working_hours_end')} />
          </Field>
        </Grid>
        <Field label="Working Days">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {DAYS.map((day) => {
              const active = (company.working_days || []).includes(day);
              return (
                <button key={day} type="button" onClick={() => toggleDay(day)} style={{
                  padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                  cursor: 'pointer', border: active ? 'none' : '1.5px solid #E5E7EB',
                  background: active ? '#2563EB' : 'white',
                  color: active ? 'white' : '#6B7280',
                  transition: 'all 0.15s',
                }}>
                  {day}
                </button>
              );
            })}
          </div>
        </Field>
      </Section>

      {/* Actions */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 32 }}>
        <button onClick={handleNext} disabled={saving} style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '12px 28px', borderRadius: 10, border: 'none',
          background: saving ? '#93C5FD' : 'linear-gradient(135deg, #2563EB, #1D4ED8)',
          color: 'white', fontSize: 14, fontWeight: 700, cursor: saving ? 'wait' : 'pointer',
          boxShadow: '0 4px 14px rgba(37,99,235,0.3)', transition: 'all 0.2s',
        }}>
          {saving ? <Loader size={14} className="animate-spin" /> : null}
          {saving ? 'Saving…' : 'Continue →'}
        </button>
      </div>
    </div>
  );
}

// ── Shared sub-components ───────────────────────────────────────────────────

function Section({ icon, title, children }) {
  return (
    <div style={{
      background: 'white', border: '1px solid #E5E7EB', borderRadius: 12,
      padding: '24px', marginBottom: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 8,
          background: '#EFF6FF',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>{icon}</div>
        <span style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>{title}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>{children}</div>
    </div>
  );
}

function Grid({ cols, children }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
      gap: 16,
    }}>
      {children}
    </div>
  );
}

function Err({ children }) {
  return <span style={{ fontSize: 11, color: '#EF4444', marginTop: 2 }}>{children}</span>;
}
