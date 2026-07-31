/**
 * Step2Factories.jsx — Add / Edit / Delete factories (Setup Wizard, Step 2).
 */

import { useState, useEffect } from 'react';
import { Factory, Plus, Pencil, Trash2, MapPin, Loader, X, AlertCircle } from 'lucide-react';
import { useSetupStore } from '../../store/setupStore';
import { listFactories, createFactory, updateFactory, deleteFactory } from '../../services/manufacturerApi';

const FACTORY_TYPES = ['Assembly', 'Fabrication', 'Foundry', 'Packaging', 'R&D', 'Warehousing', 'Other'];
const STATUSES = ['Operational', 'Under Construction', 'Maintenance', 'Idle', 'Closed'];

const inputStyle = {
  width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8,
  padding: '9px 12px', fontSize: 13.5, outline: 'none',
  background: 'white', color: '#111827', transition: 'border-color 0.15s',
  boxSizing: 'border-box',
};
const focusIn  = (e) => (e.target.style.borderColor = '#2563EB');
const focusOut = (e) => (e.target.style.borderColor = '#E5E7EB');

const EMPTY = {
  factory_name: '', factory_code: '', factory_type: 'Assembly',
  country: '', state: '', city: '', address: '',
  latitude: '', longitude: '', manufacturing_cap: '',
  operating_status: 'Operational', factory_manager: '', contact_number: '',
};

export default function Step2Factories({ onNext, onBack }) {
  const { factories, setFactories, addFactory, updateFactory: storeUpdate, removeFactory } = useSetupStore();
  const [loading,  setLoading]  = useState(true);
  const [saving,   setSaving]   = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editId,   setEditId]   = useState(null);
  const [form,     setForm]     = useState(EMPTY);
  const [errors,   setErrors]   = useState({});
  const [apiErr,   setApiErr]   = useState('');

  // Load existing factories on mount (resume support)
  useEffect(() => {
    listFactories()
      .then((data) => { setFactories(data || []); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const setF = (k) => (e) => {
    setForm((p) => ({ ...p, [k]: e.target.value }));
    if (errors[k]) setErrors((p) => ({ ...p, [k]: '' }));
  };

  function openAdd() {
    setForm(EMPTY); setEditId(null); setErrors({}); setApiErr(''); setShowForm(true);
  }

  function openEdit(factory) {
    setForm({
      factory_name:     factory.factory_name     || '',
      factory_code:     factory.factory_code     || '',
      factory_type:     factory.factory_type     || 'Assembly',
      country:          factory.country          || '',
      state:            factory.state            || '',
      city:             factory.city             || '',
      address:          factory.address          || '',
      latitude:         factory.latitude         != null ? String(factory.latitude) : '',
      longitude:        factory.longitude        != null ? String(factory.longitude) : '',
      manufacturing_cap: factory.manufacturing_cap || '',
      operating_status: factory.operating_status || 'Operational',
      factory_manager:  factory.factory_manager  || '',
      contact_number:   factory.contact_number   || '',
    });
    setEditId(factory.id); setErrors({}); setApiErr(''); setShowForm(true);
  }

  function validate() {
    const e = {};
    if (!form.factory_name.trim()) e.factory_name = 'Name is required';
    if (!form.factory_code.trim()) e.factory_code = 'Factory ID / code is required';
    if (!form.country.trim())      e.country       = 'Country is required';
    return e;
  }

  async function handleSave() {
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setSaving(true); setApiErr('');
    try {
      const payload = {
        ...form,
        latitude:  form.latitude  ? parseFloat(form.latitude)  : null,
        longitude: form.longitude ? parseFloat(form.longitude) : null,
      };
      if (editId) {
        const updated = await updateFactory(editId, payload);
        storeUpdate(editId, updated);
      } else {
        const created = await createFactory(payload);
        addFactory(created);
      }
      setShowForm(false);
    } catch (e) {
      setApiErr(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id) {
    setDeleting(id);
    try {
      await deleteFactory(id);
      removeFactory(id);
    } catch (e) {
      setApiErr(e.message);
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div style={{ maxWidth: 760, animation: 'slideUp 0.3s ease both' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: '#EFF6FF', border: '1px solid #DBEAFE',
          borderRadius: 20, padding: '4px 12px', marginBottom: 12,
        }}>
          <Factory size={13} color="#2563EB" />
          <span style={{ fontSize: 12, fontWeight: 600, color: '#2563EB' }}>Step 2 of 7</span>
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#111827', marginBottom: 6 }}>Factories</h1>
        <p style={{ fontSize: 14, color: '#6B7280' }}>
          Add all manufacturing locations. You can add, edit, and delete factories freely.
        </p>
      </div>

      {/* Factory cards */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#9CA3AF' }}>
          <Loader size={20} style={{ animation: 'spin 1s linear infinite' }} />
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
          {factories.length === 0 && !showForm && (
            <div style={{
              border: '2px dashed #E5E7EB', borderRadius: 12, padding: '32px',
              textAlign: 'center', color: '#9CA3AF',
            }}>
              <Factory size={28} color="#D1D5DB" style={{ margin: '0 auto 10px' }} />
              <p style={{ fontSize: 14, fontWeight: 600 }}>No factories added yet</p>
              <p style={{ fontSize: 12, marginTop: 4 }}>Click "Add Factory" to begin.</p>
            </div>
          )}

          {factories.map((f) => (
            <div key={f.id} style={{
              background: 'white', border: '1px solid #E5E7EB', borderRadius: 12,
              padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16,
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 10,
                background: 'linear-gradient(135deg, #EFF6FF, #DBEAFE)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}>
                <Factory size={18} color="#2563EB" />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>
                  {f.factory_name}
                  <span style={{
                    marginLeft: 8, fontSize: 11, background: '#F3F4F6',
                    borderRadius: 6, padding: '2px 7px', color: '#6B7280', fontWeight: 500,
                  }}>{f.factory_code}</span>
                </div>
                <div style={{ fontSize: 12, color: '#6B7280', marginTop: 3, display: 'flex', gap: 8 }}>
                  <span><MapPin size={10} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                    {[f.city, f.country].filter(Boolean).join(', ')}
                  </span>
                  <span>· {f.factory_type}</span>
                  <span style={{
                    color: f.operating_status === 'Operational' ? '#10B981' : '#F59E0B',
                    fontWeight: 600,
                  }}>· {f.operating_status}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                <IconBtn onClick={() => openEdit(f)} color="#2563EB" bg="#EFF6FF" title="Edit">
                  <Pencil size={13} />
                </IconBtn>
                <IconBtn
                  onClick={() => handleDelete(f.id)}
                  color="#EF4444" bg="#FEF2F2" title="Delete"
                  disabled={deleting === f.id}
                >
                  {deleting === f.id ? <Loader size={13} /> : <Trash2 size={13} />}
                </IconBtn>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Inline add/edit form */}
      {showForm && (
        <div style={{
          background: 'white', border: '1.5px solid #DBEAFE', borderRadius: 12,
          padding: '24px', marginBottom: 16, animation: 'slideDown 0.2s ease both',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>
              {editId ? 'Edit Factory' : 'New Factory'}
            </span>
            <button onClick={() => setShowForm(false)} style={{
              background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF', padding: 0,
            }}><X size={16} /></button>
          </div>

          {apiErr && (
            <div style={{
              display: 'flex', gap: 8, alignItems: 'center',
              background: '#FEF2F2', border: '1px solid #FECACA',
              borderRadius: 8, padding: '8px 12px', marginBottom: 16, fontSize: 12, color: '#DC2626',
            }}>
              <AlertCircle size={12} />{apiErr}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <FField label="Factory Name" required err={errors.factory_name}>
              <input style={inputStyle} value={form.factory_name} onChange={setF('factory_name')}
                placeholder="Main Assembly Plant" onFocus={focusIn} onBlur={focusOut} />
            </FField>
            <FField label="Factory ID / Code" required err={errors.factory_code}>
              <input style={inputStyle} value={form.factory_code} onChange={setF('factory_code')}
                placeholder="FAC-01" onFocus={focusIn} onBlur={focusOut} />
            </FField>
            <FField label="Factory Type">
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={form.factory_type}
                onChange={setF('factory_type')} onFocus={focusIn} onBlur={focusOut}>
                {FACTORY_TYPES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </FField>
            <FField label="Operating Status">
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={form.operating_status}
                onChange={setF('operating_status')} onFocus={focusIn} onBlur={focusOut}>
                {STATUSES.map((s) => <option key={s}>{s}</option>)}
              </select>
            </FField>
            <FField label="Country" required err={errors.country}>
              <input style={inputStyle} value={form.country} onChange={setF('country')}
                placeholder="India" onFocus={focusIn} onBlur={focusOut} />
            </FField>
            <FField label="State">
              <input style={inputStyle} value={form.state} onChange={setF('state')}
                placeholder="Karnataka" onFocus={focusIn} onBlur={focusOut} />
            </FField>
            <FField label="City">
              <input style={inputStyle} value={form.city} onChange={setF('city')}
                placeholder="Bengaluru" onFocus={focusIn} onBlur={focusOut} />
            </FField>
            <FField label="Manufacturing Capacity">
              <input style={inputStyle} value={form.manufacturing_cap} onChange={setF('manufacturing_cap')}
                placeholder="10,000 units/day" onFocus={focusIn} onBlur={focusOut} />
            </FField>
            <FField label="Latitude" hint="-90 to 90">
              <input style={inputStyle} type="number" value={form.latitude} onChange={setF('latitude')}
                placeholder="12.9716" onFocus={focusIn} onBlur={focusOut} />
            </FField>
            <FField label="Longitude" hint="-180 to 180">
              <input style={inputStyle} type="number" value={form.longitude} onChange={setF('longitude')}
                placeholder="77.5946" onFocus={focusIn} onBlur={focusOut} />
            </FField>
            <FField label="Factory Manager">
              <input style={inputStyle} value={form.factory_manager} onChange={setF('factory_manager')}
                placeholder="Rajesh Kumar" onFocus={focusIn} onBlur={focusOut} />
            </FField>
            <FField label="Contact Number">
              <input style={inputStyle} value={form.contact_number} onChange={setF('contact_number')}
                placeholder="+91 98765 43210" onFocus={focusIn} onBlur={focusOut} />
            </FField>
          </div>
          <div style={{ gridColumn: '1 / -1', marginTop: 4 }}>
            <FField label="Address">
              <input style={inputStyle} value={form.address} onChange={setF('address')}
                placeholder="Plot 42, Electronics City Phase II, Bengaluru 560 100"
                onFocus={focusIn} onBlur={focusOut} />
            </FField>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 18 }}>
            <button onClick={() => setShowForm(false)} style={{
              padding: '9px 20px', borderRadius: 8, border: '1.5px solid #E5E7EB',
              background: 'white', color: '#374151', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            }}>Cancel</button>
            <button onClick={handleSave} disabled={saving} style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '9px 20px', borderRadius: 8, border: 'none',
              background: '#2563EB', color: 'white', fontSize: 13, fontWeight: 600,
              cursor: saving ? 'wait' : 'pointer',
            }}>
              {saving && <Loader size={12} />}
              {saving ? 'Saving…' : editId ? 'Save Changes' : 'Add Factory'}
            </button>
          </div>
        </div>
      )}

      {/* Add factory button */}
      {!showForm && (
        <button onClick={openAdd} style={{
          display: 'flex', alignItems: 'center', gap: 8,
          width: '100%', padding: '12px 16px',
          border: '2px dashed #DBEAFE', borderRadius: 10,
          background: '#F8FAFF', color: '#2563EB',
          fontSize: 13, fontWeight: 600, cursor: 'pointer',
          marginBottom: 24, transition: 'all 0.15s',
        }}
          onMouseEnter={(e) => (e.currentTarget.style.background = '#EFF6FF')}
          onMouseLeave={(e) => (e.currentTarget.style.background = '#F8FAFF')}
        >
          <Plus size={16} />Add Factory
        </button>
      )}

      {/* Navigation */}
      <NavRow onBack={onBack} onNext={onNext} nextLabel="Continue →" />
    </div>
  );
}

// ── Shared sub-components ─────────────────────────────────────────────────

function FField({ label, required, err, hint, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <label style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}{required && <span style={{ color: '#EF4444', marginLeft: 2 }}>*</span>}
      </label>
      {children}
      {err  && <span style={{ fontSize: 10.5, color: '#EF4444' }}>{err}</span>}
      {hint && <span style={{ fontSize: 10.5, color: '#9CA3AF' }}>{hint}</span>}
    </div>
  );
}

function IconBtn({ onClick, color, bg, title, disabled, children }) {
  return (
    <button onClick={onClick} disabled={disabled} title={title} style={{
      width: 30, height: 30, borderRadius: 7, border: 'none',
      background: bg, color, display: 'flex', alignItems: 'center', justifyContent: 'center',
      cursor: disabled ? 'wait' : 'pointer', transition: 'opacity 0.15s',
      opacity: disabled ? 0.6 : 1,
    }}>
      {children}
    </button>
  );
}

function NavRow({ onBack, onNext, nextLabel = 'Continue →' }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
      <button onClick={onBack} style={{
        padding: '10px 20px', borderRadius: 8, border: '1.5px solid #E5E7EB',
        background: 'white', color: '#374151', fontSize: 13, fontWeight: 600, cursor: 'pointer',
      }}>← Back</button>
      <button onClick={onNext} style={{
        padding: '11px 26px', borderRadius: 10, border: 'none',
        background: 'linear-gradient(135deg, #2563EB, #1D4ED8)',
        color: 'white', fontSize: 14, fontWeight: 700, cursor: 'pointer',
        boxShadow: '0 4px 14px rgba(37,99,235,0.3)',
      }}>{nextLabel}</button>
    </div>
  );
}
