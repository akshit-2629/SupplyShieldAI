import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Building2, Users, MapPin, Package, Factory, Clock,
  Award, Image, ChevronRight, ChevronLeft, Check,
  ShieldCheck, Plus, Trash2, Save, AlertTriangle, Globe
} from 'lucide-react';
import {
  updateSupplierProfile, submitProductionUpdate,
  createLeadTime, getSetupStatus, markSetupComplete, getSupplierProfile
} from '../../services/supplierApi';
import { useSupplierAuth } from '../../context/SupplierAuthContext';

// ── Step metadata ─────────────────────────────────────────────────────────────
const STEPS = [
  { id: 'company',        label: 'Company Profile',     icon: Building2,  color: '#2563EB' },
  { id: 'contacts',       label: 'Contacts',            icon: Users,      color: '#7C3AED' },
  { id: 'locations',      label: 'Locations',           icon: MapPin,     color: '#DC2626' },
  { id: 'products',       label: 'Products & Components', icon: Package,  color: '#D97706' },
  { id: 'production',     label: 'Production Setup',    icon: Factory,    color: '#059669' },
  { id: 'lead_times',     label: 'Lead Times & Shipping', icon: Clock,    color: '#0891B2' },
  { id: 'certifications', label: 'Certifications',      icon: Award,      color: '#DB2777' },
  { id: 'review',         label: 'Review & Activate',   icon: ShieldCheck, color: '#10B981' },
];

const inp = {
  width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '10px 14px',
  fontSize: 14, outline: 'none', background: 'white', boxSizing: 'border-box',
  transition: 'border-color 0.15s',
};
const label = { fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 6 };
const grid2 = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 };
const focusIn = (e) => { e.target.style.borderColor = '#10B981'; };
const focusOut = (e) => { e.target.style.borderColor = '#E5E7EB'; };

// ── Shared Input component ────────────────────────────────────────────────────
function Field({ lbl, value, onChange, type = 'text', placeholder, span, options, rows }) {
  const style = span ? { ...inp, gridColumn: `span ${span}` } : inp;
  if (options) return (
    <div>
      <label style={label}>{lbl}</label>
      <select style={style} value={value} onChange={e => onChange(e.target.value)}
        onFocus={focusIn} onBlur={focusOut}>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
  if (rows) return (
    <div>
      <label style={label}>{lbl}</label>
      <textarea style={{ ...style, resize: 'vertical', minHeight: rows * 28 }}
        value={value} onChange={e => onChange(e.target.value)}
        placeholder={placeholder} onFocus={focusIn} onBlur={focusOut} />
    </div>
  );
  return (
    <div>
      <label style={label}>{lbl}</label>
      <input type={type} style={style} value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder || lbl} onFocus={focusIn} onBlur={focusOut} />
    </div>
  );
}

// ── Step 1: Company Profile ───────────────────────────────────────────────────
function Step1({ data, set }) {
  return (
    <div style={{ display: 'grid', gap: 16, gridTemplateColumns: '1fr 1fr' }}>
      <div style={{ gridColumn: 'span 2' }}>
        <Field lbl="Company Name *" value={data.company_name} onChange={v => set('company_name', v)} placeholder="Acme Electronics Ltd." />
      </div>
      <Field lbl="Legal Name" value={data.legal_name} onChange={v => set('legal_name', v)} placeholder="Legal entity name" />
      <Field lbl="Registration Number" value={data.registration_number} onChange={v => set('registration_number', v)} />
      <Field lbl="Tax ID / VAT Number" value={data.tax_id} onChange={v => set('tax_id', v)} />
      <Field lbl="Year Established" type="number" value={data.year_established} onChange={v => set('year_established', v)} placeholder="2005" />
      <Field lbl="Number of Employees" type="number" value={data.employee_count} onChange={v => set('employee_count', v)} />
      <Field lbl="Annual Revenue (USD)" value={data.annual_revenue_usd} onChange={v => set('annual_revenue_usd', v)} placeholder="e.g. $50M" />
      <Field lbl="Website" value={data.website} onChange={v => set('website', v)} placeholder="https://example.com" />
      <Field lbl="Headquarters Country *" value={data.headquarters_country} onChange={v => set('headquarters_country', v)} placeholder="United States" />
      <Field lbl="Headquarters City" value={data.headquarters_city} onChange={v => set('headquarters_city', v)} />
      <Field lbl="Headquarters Address" value={data.headquarters_address} onChange={v => set('headquarters_address', v)} placeholder="Street, postal code" />
      <Field lbl="Business Email" type="email" value={data.email} onChange={v => set('email', v)} />
      <Field lbl="Phone Number" type="tel" value={data.phone} onChange={v => set('phone', v)} />
      <div style={{ gridColumn: 'span 2' }}>
        <Field lbl="Business Description *" value={data.description} onChange={v => set('description', v)} rows={4} placeholder="Describe your company, what you manufacture, and your core strengths…" />
      </div>
      <div style={{ gridColumn: 'span 2' }}>
        <label style={label}>Manufacturing Categories</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {['Electronics', 'Semiconductors', 'Automotive', 'Aerospace', 'Medical Devices', 'Industrial Machinery', 'Consumer Goods', 'Chemicals', 'Packaging', 'Other'].map(cat => (
            <button key={cat} type="button"
              onClick={() => {
                const cur = data.manufacturing_categories || [];
                set('manufacturing_categories', cur.includes(cat) ? cur.filter(c => c !== cat) : [...cur, cat]);
              }}
              style={{
                padding: '5px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: 'pointer',
                border: '1.5px solid',
                borderColor: (data.manufacturing_categories || []).includes(cat) ? '#10B981' : '#E5E7EB',
                background: (data.manufacturing_categories || []).includes(cat) ? '#ECFDF5' : 'white',
                color: (data.manufacturing_categories || []).includes(cat) ? '#059669' : '#6B7280',
                transition: 'all 0.15s',
              }}>
              {cat}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Step 2: Contacts ──────────────────────────────────────────────────────────
function ContactCard({ title, contact, onChange, required }) {
  const set = (k, v) => onChange({ ...contact, [k]: v });
  return (
    <div style={{ background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 12, padding: 20, marginBottom: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: '#374151', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Users size={15} color="#10B981" /> {title} {required && <span style={{ color: '#EF4444', fontSize: 11 }}>*</span>}
      </div>
      <div style={{ ...grid2, gap: 12 }}>
        <Field lbl="Full Name" value={contact.name || ''} onChange={v => set('name', v)} />
        <Field lbl="Title / Position" value={contact.title || ''} onChange={v => set('title', v)} placeholder="VP Operations" />
        <Field lbl="Email" type="email" value={contact.email || ''} onChange={v => set('email', v)} />
        <Field lbl="Phone" type="tel" value={contact.phone || ''} onChange={v => set('phone', v)} />
      </div>
    </div>
  );
}

function Step2({ data, set }) {
  const contacts = data.contacts || [{ type: 'primary' }, { type: 'secondary' }, { type: 'emergency' }];
  const update = (i, v) => { const c = [...contacts]; c[i] = v; set('contacts', c); };
  return (
    <div>
      <ContactCard title="Primary Contact" required contact={contacts[0] || {}} onChange={v => update(0, { ...v, type: 'primary' })} />
      <ContactCard title="Secondary Contact" contact={contacts[1] || {}} onChange={v => update(1, { ...v, type: 'secondary' })} />
      <ContactCard title="Emergency Contact" contact={contacts[2] || {}} onChange={v => update(2, { ...v, type: 'emergency' })} />
    </div>
  );
}

// ── Step 3: Locations ─────────────────────────────────────────────────────────
function LocationItem({ loc, onChange, onRemove, idx }) {
  const set = (k, v) => onChange({ ...loc, [k]: v });
  return (
    <div style={{ background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 12, padding: 18, marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          {['factory', 'warehouse'].map(t => (
            <button key={t} type="button" onClick={() => set('type', t)}
              style={{ padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: 'pointer', border: '1.5px solid', transition: 'all 0.15s',
                borderColor: loc.type === t ? '#10B981' : '#E5E7EB',
                background: loc.type === t ? '#ECFDF5' : 'white',
                color: loc.type === t ? '#059669' : '#6B7280',
              }}>
              {t === 'factory' ? '🏭 Factory' : '🏪 Warehouse'}
            </button>
          ))}
        </div>
        {idx > 0 && <button type="button" onClick={onRemove} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#EF4444' }}><Trash2 size={15} /></button>}
      </div>
      <div style={{ ...grid2, gap: 12 }}>
        <Field lbl="Location Name" value={loc.name || ''} onChange={v => set('name', v)} placeholder="Main Factory — Taiwan" />
        <Field lbl="Country" value={loc.country || ''} onChange={v => set('country', v)} />
        <Field lbl="City" value={loc.city || ''} onChange={v => set('city', v)} />
        <Field lbl="Address" value={loc.address || ''} onChange={v => set('address', v)} />
        {loc.type === 'factory' && <Field lbl="Capacity (units/month)" type="number" value={loc.capacity_units || ''} onChange={v => set('capacity_units', Number(v))} />}
        <Field lbl="Notes" value={loc.notes || ''} onChange={v => set('notes', v)} />
      </div>
    </div>
  );
}

function Step3({ data, set }) {
  const locs = data.locations || [{ type: 'factory' }];
  const update = (i, v) => { const a = [...locs]; a[i] = v; set('locations', a); };
  const add = () => set('locations', [...locs, { type: 'factory' }]);
  const remove = (i) => set('locations', locs.filter((_, ii) => ii !== i));
  return (
    <div>
      {locs.map((l, i) => <LocationItem key={i} idx={i} loc={l} onChange={v => update(i, v)} onRemove={() => remove(i)} />)}
      <button type="button" onClick={add}
        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', border: '1.5px dashed #D1FAE5', borderRadius: 10, background: 'transparent', color: '#10B981', fontSize: 13, fontWeight: 600, cursor: 'pointer', width: '100%', justifyContent: 'center' }}>
        <Plus size={15} /> Add Location
      </button>
    </div>
  );
}

// ── Step 4: Products & Components ─────────────────────────────────────────────
function ProductItem({ prod, onChange, onRemove, idx }) {
  const set = (k, v) => onChange({ ...prod, [k]: v });
  return (
    <div style={{ background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 10, padding: 14, marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: '#374151' }}>Product / Component #{idx + 1}</span>
        {idx > 0 && <button type="button" onClick={onRemove} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#EF4444' }}><Trash2 size={14} /></button>}
      </div>
      <div style={{ ...grid2, gap: 10 }}>
        <Field lbl="Product Name *" value={prod.name || ''} onChange={v => set('name', v)} />
        <Field lbl="SKU / Part Number" value={prod.sku || ''} onChange={v => set('sku', v)} />
        <Field lbl="Unit (pcs/kg/m)" value={prod.unit || ''} onChange={v => set('unit', v)} placeholder="pcs" />
        <Field lbl="Description" value={prod.description || ''} onChange={v => set('description', v)} />
      </div>
    </div>
  );
}

function Step4({ data, set }) {
  const prods = data.products || [{}];
  const update = (i, v) => { const a = [...prods]; a[i] = v; set('products', a); };
  const add = () => set('products', [...prods, {}]);
  const remove = (i) => set('products', prods.filter((_, ii) => ii !== i));
  return (
    <div>
      {prods.map((p, i) => <ProductItem key={i} idx={i} prod={p} onChange={v => update(i, v)} onRemove={() => remove(i)} />)}
      <button type="button" onClick={add}
        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', border: '1.5px dashed #D1FAE5', borderRadius: 10, background: 'transparent', color: '#10B981', fontSize: 13, fontWeight: 600, cursor: 'pointer', width: '100%', justifyContent: 'center' }}>
        <Plus size={15} /> Add Product / Component
      </button>
    </div>
  );
}

// ── Step 5: Production Setup ──────────────────────────────────────────────────
function Step5({ data, set }) {
  return (
    <div style={{ ...grid2, gap: 16 }}>
      <Field lbl="Max Capacity (units/month) *" type="number" value={data.maximum_capacity_units} onChange={v => set('maximum_capacity_units', Number(v))} placeholder="10000" />
      <Field lbl="Current Output (units/month)" type="number" value={data.current_output_units} onChange={v => set('current_output_units', Number(v))} />
      <Field lbl="Shifts Per Day" options={['1', '2', '3']} value={String(data.shifts_per_day || '1')} onChange={v => set('shifts_per_day', Number(v))} />
      <Field lbl="Workforce Count" type="number" value={data.workforce_count} onChange={v => set('workforce_count', Number(v))} />
      <Field lbl="Factory Status" options={['OPERATIONAL', 'PARTIAL', 'MAINTENANCE', 'OFFLINE']} value={data.factory_status || 'OPERATIONAL'} onChange={v => set('factory_status', v)} />
      <Field lbl="Production Rate (units/day)" type="number" value={data.production_rate_per_day} onChange={v => set('production_rate_per_day', Number(v))} />
      <Field lbl="Planned Downtime Days/Month" type="number" value={data.planned_downtime_days} onChange={v => set('planned_downtime_days', Number(v))} placeholder="0" />
      <Field lbl="Next Maintenance Date" type="date" value={data.next_maintenance_date} onChange={v => set('next_maintenance_date', v)} />
      <div style={{ gridColumn: 'span 2' }}>
        <Field lbl="Production Notes" value={data.notes} onChange={v => set('notes', v)} rows={3} placeholder="Describe any current production constraints, specialisations, or notes for buyers…" />
      </div>
    </div>
  );
}

// ── Step 6: Lead Times & Shipping ─────────────────────────────────────────────
function Step6({ data, set }) {
  const INCOTERMS = ['EXW', 'FCA', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP', 'FAS', 'FOB', 'CFR', 'CIF'];
  const SHIPPING  = ['Air Freight', 'Sea Freight', 'Road Freight', 'Rail Freight', 'Express Courier', 'Multimodal'];
  const toggleList = (key, val) => {
    const cur = data[key] || [];
    set(key, cur.includes(val) ? cur.filter(v => v !== val) : [...cur, val]);
  };
  return (
    <div style={{ ...grid2, gap: 16 }}>
      <Field lbl="Standard Lead Time (days) *" type="number" value={data.standard_lead_time_days} onChange={v => set('standard_lead_time_days', Number(v))} placeholder="30" />
      <Field lbl="Expedited Lead Time (days)" type="number" value={data.expedited_lead_time_days} onChange={v => set('expedited_lead_time_days', Number(v))} placeholder="10" />
      <Field lbl="Min Order Quantity" type="number" value={data.minimum_order_quantity} onChange={v => set('minimum_order_quantity', Number(v))} placeholder="100" />
      <Field lbl="Payment Terms" value={data.payment_terms} onChange={v => set('payment_terms', v)} placeholder="Net 30 / 30% advance" />
      <div style={{ gridColumn: 'span 2' }}>
        <label style={label}>Accepted Incoterms</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {INCOTERMS.map(t => (
            <button key={t} type="button" onClick={() => toggleList('incoterms_accepted', t)}
              style={{ padding: '5px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: 'pointer', border: '1.5px solid', transition: 'all 0.15s',
                borderColor: (data.incoterms_accepted || []).includes(t) ? '#10B981' : '#E5E7EB',
                background: (data.incoterms_accepted || []).includes(t) ? '#ECFDF5' : 'white',
                color: (data.incoterms_accepted || []).includes(t) ? '#059669' : '#6B7280',
              }}>{t}</button>
          ))}
        </div>
      </div>
      <div style={{ gridColumn: 'span 2' }}>
        <label style={label}>Shipping Methods</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {SHIPPING.map(s => (
            <button key={s} type="button" onClick={() => toggleList('shipping_methods', s)}
              style={{ padding: '5px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: 'pointer', border: '1.5px solid', transition: 'all 0.15s',
                borderColor: (data.shipping_methods || []).includes(s) ? '#10B981' : '#E5E7EB',
                background: (data.shipping_methods || []).includes(s) ? '#ECFDF5' : 'white',
                color: (data.shipping_methods || []).includes(s) ? '#059669' : '#6B7280',
              }}>{s}</button>
          ))}
        </div>
      </div>
      <div style={{ gridColumn: 'span 2' }}>
        <Field lbl="Countries Served (comma-separated)" value={data.countries_served} onChange={v => set('countries_served', v)} placeholder="US, EU, Japan, India…" />
      </div>
      <div style={{ gridColumn: 'span 2' }}>
        <Field lbl="Lead Time Notes" value={data.notes} onChange={v => set('notes', v)} rows={3} placeholder="Any seasonal variations, MOQ exceptions, rush order policies…" />
      </div>
    </div>
  );
}

// ── Step 7: Certifications ────────────────────────────────────────────────────
const COMMON_CERTS = ['ISO 9001:2015', 'ISO 14001:2015', 'ISO 45001:2018', 'ISO 13485', 'IATF 16949', 'AS9100D', 'RoHS', 'REACH', 'CE Mark', 'UL', 'FCC', 'SAP ARIBA Certified'];

function CertItem({ cert, onChange, onRemove, idx }) {
  const set = (k, v) => onChange({ ...cert, [k]: v });
  return (
    <div style={{ background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 10, padding: 14, marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: '#374151' }}>{cert.name || `Certification #${idx + 1}`}</span>
        <button type="button" onClick={onRemove} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#EF4444' }}><Trash2 size={14} /></button>
      </div>
      <div style={{ ...grid2, gap: 10 }}>
        <Field lbl="Certificate Name *" value={cert.name || ''} onChange={v => set('name', v)} placeholder="ISO 9001:2015" />
        <Field lbl="Issuing Body" value={cert.issuing_body || ''} onChange={v => set('issuing_body', v)} placeholder="Bureau Veritas" />
        <Field lbl="Issue Date" type="date" value={cert.issued_date || ''} onChange={v => set('issued_date', v)} />
        <Field lbl="Expiry Date" type="date" value={cert.expiry_date || ''} onChange={v => set('expiry_date', v)} />
      </div>
    </div>
  );
}

function Step7({ data, set }) {
  const certs = data.certifications || [];
  const update = (i, v) => { const a = [...certs]; a[i] = v; set('certifications', a); };
  const add = (name = '') => set('certifications', [...certs, { name }]);
  const remove = (i) => set('certifications', certs.filter((_, ii) => ii !== i));
  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <label style={label}>Quick-add common certifications</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {COMMON_CERTS.filter(c => !certs.some(x => x.name === c)).map(c => (
            <button key={c} type="button" onClick={() => add(c)}
              style={{ padding: '5px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: 'pointer', border: '1.5px solid #E5E7EB', background: 'white', color: '#374151', transition: 'all 0.15s' }}
              onMouseEnter={e => { e.target.style.borderColor='#10B981'; e.target.style.color='#059669'; }}
              onMouseLeave={e => { e.target.style.borderColor='#E5E7EB'; e.target.style.color='#374151'; }}>
              + {c}
            </button>
          ))}
        </div>
      </div>
      {certs.map((c, i) => <CertItem key={i} idx={i} cert={c} onChange={v => update(i, v)} onRemove={() => remove(i)} />)}
      <button type="button" onClick={() => add()}
        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', border: '1.5px dashed #D1FAE5', borderRadius: 10, background: 'transparent', color: '#10B981', fontSize: 13, fontWeight: 600, cursor: 'pointer', width: '100%', justifyContent: 'center', marginTop: 8 }}>
        <Plus size={15} /> Add Custom Certification
      </button>
    </div>
  );
}

// ── Step 8: Review & Activate ─────────────────────────────────────────────────
function ReviewRow({ label: lbl, value, ok }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #F3F4F6' }}>
      <span style={{ fontSize: 13, color: '#6B7280' }}>{lbl}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>{value}</span>
        {ok ? <Check size={14} color="#10B981" /> : <AlertTriangle size={14} color="#F59E0B" />}
      </div>
    </div>
  );
}

function Step8({ profile, production, leadTime }) {
  return (
    <div>
      <div style={{ background: 'linear-gradient(135deg, #ECFDF5, #D1FAE5)', border: '1px solid #A7F3D0', borderRadius: 14, padding: 24, marginBottom: 24, textAlign: 'center' }}>
        <ShieldCheck size={44} color="#10B981" style={{ marginBottom: 12 }} />
        <h3 style={{ fontSize: 20, fontWeight: 800, color: '#065F46', marginBottom: 8 }}>Ready to Activate!</h3>
        <p style={{ fontSize: 14, color: '#047857' }}>Review your setup summary below. Once activated, your data will power the SupplyShield AI platform.</p>
      </div>
      <div style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 12, padding: '0 20px' }}>
        <ReviewRow label="Company Name" value={profile.company_name || '—'} ok={!!profile.company_name} />
        <ReviewRow label="Country" value={profile.headquarters_country || '—'} ok={!!profile.headquarters_country} />
        <ReviewRow label="Description" value={profile.description ? '✓ Provided' : 'Missing'} ok={!!profile.description} />
        <ReviewRow label="Primary Contact" value={profile.contacts?.[0]?.name || '—'} ok={!!profile.contacts?.[0]?.name} />
        <ReviewRow label="Locations" value={`${(profile.locations || []).length} configured`} ok={(profile.locations || []).length > 0} />
        <ReviewRow label="Products" value={`${(profile.products || []).length} added`} ok={(profile.products || []).length > 0} />
        <ReviewRow label="Max Capacity" value={production.maximum_capacity_units ? `${production.maximum_capacity_units.toLocaleString()} units/mo` : '—'} ok={!!production.maximum_capacity_units} />
        <ReviewRow label="Standard Lead Time" value={leadTime.standard_lead_time_days ? `${leadTime.standard_lead_time_days} days` : '—'} ok={!!leadTime.standard_lead_time_days} />
        <ReviewRow label="Certifications" value={`${(profile.certifications || []).length} added`} ok={(profile.certifications || []).length > 0} />
      </div>
    </div>
  );
}

// ── Main Wizard ───────────────────────────────────────────────────────────────
export default function SupplierSetup() {
  const navigate = useNavigate();
  const { supplierUser } = useSupplierAuth();

  const [step, setStep]       = useState(0);
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState('');
  const [activating, setActivating] = useState(false);

  // Profile data
  const [profile, setProfile] = useState({
    company_name: '', legal_name: '', registration_number: '', tax_id: '',
    year_established: '', employee_count: '', annual_revenue_usd: '', description: '',
    website: '', headquarters_address: '', headquarters_country: '', headquarters_city: '',
    email: '', phone: '', contacts: [], locations: [], products: [],
    manufacturing_categories: [], certifications: [],
  });

  // Production data
  const [production, setProduction] = useState({
    maximum_capacity_units: '', current_output_units: '', shifts_per_day: 1,
    workforce_count: '', factory_status: 'OPERATIONAL', production_rate_per_day: '',
    planned_downtime_days: 0, notes: '',
  });

  // Lead time data
  const [leadTime, setLeadTime] = useState({
    standard_lead_time_days: '', expedited_lead_time_days: '', minimum_order_quantity: '',
    payment_terms: '', incoterms_accepted: [], shipping_methods: [], countries_served: '', notes: '',
  });

  const setP  = (k, v) => setProfile(p => ({ ...p, [k]: v }));
  const setProd = (k, v) => setProduction(p => ({ ...p, [k]: v }));
  const setLT = (k, v) => setLeadTime(p => ({ ...p, [k]: v }));

  // Load saved profile from PostgreSQL database on mount
  useEffect(() => {
    async function loadSavedProfile() {
      try {
        const p = await getSupplierProfile();
        if (p) {
          setProfile(prev => ({
            ...prev,
            company_name: p.company_name || prev.company_name,
            legal_name: p.legal_name || prev.legal_name,
            registration_number: p.registration_number || prev.registration_number,
            tax_id: p.tax_id || prev.tax_id,
            year_established: p.year_established || prev.year_established,
            employee_count: p.employee_count || prev.employee_count,
            annual_revenue_usd: p.annual_revenue_usd || prev.annual_revenue_usd,
            description: p.description || prev.description,
            website: p.website || prev.website,
            headquarters_address: p.headquarters_address || prev.headquarters_address,
            headquarters_country: p.headquarters_country || prev.headquarters_country,
            headquarters_city: p.headquarters_city || prev.headquarters_city,
            email: p.email || prev.email,
            phone: p.phone || prev.phone,
            contacts: Array.isArray(p.contacts) && p.contacts.length ? p.contacts : prev.contacts,
            locations: Array.isArray(p.locations) ? p.locations : prev.locations,
            products: Array.isArray(p.products) ? p.products : prev.products,
            manufacturing_categories: Array.isArray(p.manufacturing_categories) ? p.manufacturing_categories : prev.manufacturing_categories,
            certifications: Array.isArray(p.certifications) ? p.certifications : prev.certifications,
          }));
        }
      } catch (_) {}
    }
    loadSavedProfile();
  }, []);

  // Pre-fill from auth metadata without overwriting existing company_name
  useEffect(() => {
    if (supplierUser?.user_metadata) {
      const m = supplierUser.user_metadata;
      const metaName = m.companyName || m.company_name;
      setProfile(p => ({
        ...p,
        company_name: p.company_name || metaName || '',
        email: p.email || supplierUser.email || '',
        contacts: p.contacts.length ? p.contacts : [{ type: 'primary', name: m.contactName || m.contact_name || '', email: supplierUser.email || '' }],
      }));
    }
  }, [supplierUser]);

  async function saveCurrentStep() {
    setSaving(true);
    setError('');
    try {
      if (step <= 3 || step === 6) {
        // Steps 0-3 (company, contacts, locations, products) + 6 (certifications) → save profile
        await updateSupplierProfile(profile);
      } else if (step === 4) {
        await submitProductionUpdate(production);
      } else if (step === 5) {
        await createLeadTime(leadTime);
      }
    } catch (err) {
      setError(err.message || 'Save failed. Please try again.');
      setSaving(false);
      return false;
    }
    setSaving(false);
    return true;
  }

  async function handleNext() {
    const ok = await saveCurrentStep();
    if (ok) setStep(s => Math.min(s + 1, STEPS.length - 1));
  }

  async function handleActivate() {
    setActivating(true);
    setError('');
    try {
      await updateSupplierProfile(profile);
      await markSetupComplete();
      navigate('/supplier/dashboard', { replace: true });
    } catch (err) {
      setError(err.message || 'Activation failed');
      setActivating(false);
    }
  }

  const isLast = step === STEPS.length - 1;
  const progress = ((step) / (STEPS.length - 1)) * 100;

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 50%, #F9FAFB 100%)', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px 20px' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        style={{ textAlign: 'center', marginBottom: 36 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 12 }}>
          <div style={{ width: 40, height: 40, background: 'linear-gradient(135deg, #10B981, #059669)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldCheck size={22} color="white" />
          </div>
          <span style={{ fontSize: 18, fontWeight: 800, color: '#111827' }}>SupplyShield AI</span>
        </div>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: '#111827', marginBottom: 8 }}>Initial Business Setup</h1>
        <p style={{ fontSize: 15, color: '#6B7280' }}>Complete your profile to activate the Supplier Portal — Step {step + 1} of {STEPS.length}</p>
      </motion.div>

      {/* Progress bar */}
      <div style={{ width: '100%', maxWidth: 820, marginBottom: 32 }}>
        <div style={{ background: '#E5E7EB', borderRadius: 99, height: 6, overflow: 'hidden' }}>
          <motion.div animate={{ width: `${progress}%` }} transition={{ duration: 0.4 }}
            style={{ height: '100%', background: 'linear-gradient(90deg, #10B981, #059669)', borderRadius: 99 }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10 }}>
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={s.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <div style={{
                  width: 30, height: 30, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: i < step ? '#10B981' : i === step ? s.color : '#E5E7EB',
                  transition: 'all 0.3s',
                }}>
                  {i < step ? <Check size={14} color="white" /> : <Icon size={13} color={i === step ? 'white' : '#9CA3AF'} />}
                </div>
                <span style={{ fontSize: 9, color: i === step ? s.color : '#9CA3AF', fontWeight: i === step ? 700 : 400, textAlign: 'center', maxWidth: 60 }}>{s.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Card */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} key={step}
        style={{ width: '100%', maxWidth: 820, background: 'white', borderRadius: 20, boxShadow: '0 4px 40px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        {/* Card header */}
        <div style={{ padding: '22px 32px', borderBottom: '1px solid #F3F4F6', background: '#FAFAFA', display: 'flex', alignItems: 'center', gap: 14 }}>
          {(() => { const Icon = STEPS[step].icon; return <div style={{ width: 40, height: 40, borderRadius: 12, background: STEPS[step].color + '18', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Icon size={20} color={STEPS[step].color} /></div>; })()}
          <div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#111827' }}>{STEPS[step].label}</div>
            <div style={{ fontSize: 12, color: '#9CA3AF' }}>Step {step + 1} of {STEPS.length}</div>
          </div>
          <div style={{ marginLeft: 'auto', fontSize: 12, fontWeight: 600, color: '#10B981', background: '#ECFDF5', borderRadius: 99, padding: '4px 12px' }}>
            {Math.round(progress)}% Complete
          </div>
        </div>

        {/* Step content */}
        <div style={{ padding: '28px 32px', maxHeight: '55vh', overflowY: 'auto' }}>
          <AnimatePresence mode="wait">
            <motion.div key={step} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }}>
              {step === 0 && <Step1 data={profile} set={setP} />}
              {step === 1 && <Step2 data={profile} set={setP} />}
              {step === 2 && <Step3 data={profile} set={setP} />}
              {step === 3 && <Step4 data={profile} set={setP} />}
              {step === 4 && <Step5 data={production} set={setProd} />}
              {step === 5 && <Step6 data={leadTime} set={setLT} />}
              {step === 6 && <Step7 data={profile} set={setP} />}
              {step === 7 && <Step8 profile={profile} production={production} leadTime={leadTime} />}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div style={{ padding: '18px 32px', borderTop: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#FAFAFA' }}>
          <button onClick={() => setStep(s => Math.max(s - 1, 0))} disabled={step === 0}
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', border: '1.5px solid #E5E7EB', borderRadius: 10, background: 'white', color: '#374151', fontSize: 14, fontWeight: 600, cursor: step === 0 ? 'default' : 'pointer', opacity: step === 0 ? 0.4 : 1 }}>
            <ChevronLeft size={16} /> Back
          </button>

          {error && <div style={{ flex: 1, textAlign: 'center', fontSize: 13, color: '#EF4444', fontWeight: 600 }}>{error}</div>}

          {isLast ? (
            <button onClick={handleActivate} disabled={activating}
              style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '11px 28px', border: 'none', borderRadius: 10, background: activating ? '#D1FAE5' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', fontSize: 14, fontWeight: 700, cursor: activating ? 'default' : 'pointer', boxShadow: '0 4px 12px rgba(16,185,129,0.3)' }}>
              <ShieldCheck size={16} /> {activating ? 'Activating…' : 'Activate Portal'}
            </button>
          ) : (
            <button onClick={handleNext} disabled={saving}
              style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '11px 24px', border: 'none', borderRadius: 10, background: saving ? '#D1FAE5' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', fontSize: 14, fontWeight: 700, cursor: saving ? 'default' : 'pointer' }}>
              {saving ? 'Saving…' : 'Save & Continue'} <ChevronRight size={16} />
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
