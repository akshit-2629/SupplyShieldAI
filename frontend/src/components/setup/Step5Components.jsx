/**
 * Step5Components.jsx — Bill of Materials / component library (Setup Wizard, Step 5).
 * Components can be linked to a product via product_id dropdown.
 */

import { useState, useEffect } from 'react';
import { Cpu, Plus, Pencil, Trash2, Loader, X, AlertCircle } from 'lucide-react';
import { useSetupStore } from '../../store/setupStore';
import {
  listComponents, createComponent, updateComponent, deleteComponent,
} from '../../services/manufacturerApi';

const COMP_CATEGORIES = [
  'Electronic', 'Mechanical', 'Optical', 'Chemical', 'Structural',
  'Thermal', 'Electrical', 'Software / Firmware', 'Packaging', 'Raw Material', 'Other',
];
const CRITICALITIES = ['Low', 'Medium', 'High', 'Critical'];
const UNITS = ['units', 'kg', 'g', 'litres', 'ml', 'metres', 'pcs', 'sets'];

const CRIT_COLORS = { Low: '#10B981', Medium: '#F59E0B', High: '#F97316', Critical: '#EF4444' };

const inputStyle = {
  width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8,
  padding: '9px 12px', fontSize: 13.5, outline: 'none',
  background: 'white', color: '#111827', transition: 'border-color 0.15s', boxSizing: 'border-box',
};
const fi = (e) => (e.target.style.borderColor = '#2563EB');
const fo = (e) => (e.target.style.borderColor = '#E5E7EB');

const EMPTY = {
  product_id: '', component_name: '', category: 'Electronic',
  criticality: 'Medium', preferred_supplier: '', safety_stock: '0',
  unit: 'units', avg_monthly_usage: '',
};

export default function Step5Components({ onNext, onBack }) {
  const {
    components, products, setComponents, addComponent,
    updateComponent: storeUpd, removeComponent,
  } = useSetupStore();

  const [loading,  setLoading]  = useState(true);
  const [saving,   setSaving]   = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editId,   setEditId]   = useState(null);
  const [form,     setForm]     = useState(EMPTY);
  const [errors,   setErrors]   = useState({});
  const [apiErr,   setApiErr]   = useState('');
  const [filterProd, setFilterProd] = useState('');

  useEffect(() => {
    listComponents()
      .then((d) => setComponents(d || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const setF = (k) => (e) => {
    setForm((p) => ({ ...p, [k]: e.target.value }));
    if (errors[k]) setErrors((p) => ({ ...p, [k]: '' }));
  };

  function openAdd() { setForm(EMPTY); setEditId(null); setErrors({}); setApiErr(''); setShowForm(true); }

  function openEdit(c) {
    setForm({
      product_id:         c.product_id         || '',
      component_name:     c.component_name     || '',
      category:           c.category           || 'Electronic',
      criticality:        c.criticality        || 'Medium',
      preferred_supplier: c.preferred_supplier || '',
      safety_stock:       c.safety_stock != null ? String(c.safety_stock) : '0',
      unit:               c.unit               || 'units',
      avg_monthly_usage:  c.avg_monthly_usage  != null ? String(c.avg_monthly_usage) : '',
    });
    setEditId(c.id); setErrors({}); setApiErr(''); setShowForm(true);
  }

  function validate() {
    const e = {};
    if (!form.component_name.trim()) e.component_name = 'Name required';
    return e;
  }

  async function handleSave() {
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setSaving(true); setApiErr('');
    try {
      const payload = {
        ...form,
        product_id:        form.product_id || null,
        safety_stock:      parseInt(form.safety_stock, 10) || 0,
        avg_monthly_usage: form.avg_monthly_usage ? parseInt(form.avg_monthly_usage, 10) : null,
      };
      if (editId) {
        const u = await updateComponent(editId, payload);
        storeUpd(editId, u);
      } else {
        const c = await createComponent(payload);
        addComponent(c);
      }
      setShowForm(false);
    } catch (e) { setApiErr(e.message); }
    finally { setSaving(false); }
  }

  async function handleDelete(id) {
    setDeleting(id);
    try { await deleteComponent(id); removeComponent(id); }
    catch (e) { setApiErr(e.message); }
    finally { setDeleting(null); }
  }

  const productName = (id) => products.find((p) => p.id === id)?.product_name || null;

  const filtered = filterProd
    ? components.filter((c) => c.product_id === filterProd)
    : components;

  return (
    <div style={{ maxWidth: 760, animation: 'slideUp 0.3s ease both' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: '#EFF6FF', border: '1px solid #DBEAFE',
          borderRadius: 20, padding: '4px 12px', marginBottom: 12,
        }}>
          <Cpu size={13} color="#2563EB" />
          <span style={{ fontSize: 12, fontWeight: 600, color: '#2563EB' }}>Step 5 of 7</span>
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#111827', marginBottom: 6 }}>Components</h1>
        <p style={{ fontSize: 14, color: '#6B7280' }}>
          Define the components and materials that go into your products. This builds your Bill of Materials.
        </p>
      </div>

      {/* Product filter */}
      {products.length > 0 && (
        <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <FilterPill active={!filterProd} onClick={() => setFilterProd('')}>All</FilterPill>
          {products.map((p) => (
            <FilterPill key={p.id} active={filterProd === p.id}
              onClick={() => setFilterProd(filterProd === p.id ? '' : p.id)}>
              {p.product_name}
            </FilterPill>
          ))}
        </div>
      )}

      {/* Component list */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Loader size={20} style={{ animation: 'spin 1s linear infinite', color: '#9CA3AF' }} />
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
          {filtered.length === 0 && !showForm && (
            <div style={{
              border: '2px dashed #E5E7EB', borderRadius: 12, padding: 32,
              textAlign: 'center', color: '#9CA3AF',
            }}>
              <Cpu size={28} color="#D1D5DB" style={{ margin: '0 auto 10px' }} />
              <p style={{ fontSize: 14, fontWeight: 600 }}>No components yet</p>
              <p style={{ fontSize: 12, marginTop: 4 }}>e.g. OLED Display, Processor, Battery, Camera Sensor</p>
            </div>
          )}

          {filtered.map((c) => (
            <div key={c.id} style={{
              background: 'white', border: '1px solid #E5E7EB', borderRadius: 10,
              padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 14,
            }}>
              {/* Criticality stripe */}
              <div style={{
                width: 4, height: 40, borderRadius: 4,
                background: CRIT_COLORS[c.criticality] || '#E5E7EB', flexShrink: 0,
              }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13.5, fontWeight: 700, color: '#111827' }}>
                  {c.component_name}
                </div>
                <div style={{ fontSize: 11, color: '#6B7280', marginTop: 2, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <span>{c.category}</span>
                  <span style={{ color: CRIT_COLORS[c.criticality], fontWeight: 600 }}>· {c.criticality}</span>
                  {c.product_id && <span>· {productName(c.product_id) || c.product_id}</span>}
                  {c.avg_monthly_usage && <span>· {c.avg_monthly_usage.toLocaleString()} {c.unit}/mo</span>}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                <IBtn onClick={() => openEdit(c)} col="#2563EB" bg="#EFF6FF"><Pencil size={12} /></IBtn>
                <IBtn onClick={() => handleDelete(c.id)} col="#EF4444" bg="#FEF2F2" disabled={deleting === c.id}>
                  {deleting === c.id ? <Loader size={12} /> : <Trash2 size={12} />}
                </IBtn>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Inline form */}
      {showForm && (
        <div style={{
          background: 'white', border: '1.5px solid #DBEAFE', borderRadius: 12,
          padding: 24, marginBottom: 16, animation: 'slideDown 0.2s ease both',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 18 }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>
              {editId ? 'Edit Component' : 'New Component'}
            </span>
            <button onClick={() => setShowForm(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}>
              <X size={16} />
            </button>
          </div>

          {apiErr && (
            <div style={{ display:'flex',gap:8,alignItems:'center',background:'#FEF2F2',border:'1px solid #FECACA',borderRadius:8,padding:'8px 12px',marginBottom:14,fontSize:12,color:'#DC2626' }}>
              <AlertCircle size={12}/>{apiErr}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <FField label="Component Name" required err={errors.component_name}>
              <input style={inputStyle} value={form.component_name} onChange={setF('component_name')}
                placeholder="OLED Display" onFocus={fi} onBlur={fo} />
            </FField>

            <FField label="Product (optional)">
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={form.product_id}
                onChange={setF('product_id')} onFocus={fi} onBlur={fo}>
                <option value="">— Not linked to specific product —</option>
                {products.map((p) => <option key={p.id} value={p.id}>{p.product_name}</option>)}
              </select>
            </FField>

            <FField label="Category">
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={form.category}
                onChange={setF('category')} onFocus={fi} onBlur={fo}>
                {COMP_CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </FField>

            <FField label="Criticality">
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={form.criticality}
                onChange={setF('criticality')} onFocus={fi} onBlur={fo}>
                {CRITICALITIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </FField>

            <FField label="Preferred Supplier">
              <input style={inputStyle} value={form.preferred_supplier} onChange={setF('preferred_supplier')}
                placeholder="Samsung SDI" onFocus={fi} onBlur={fo} />
            </FField>

            <FField label="Unit">
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={form.unit}
                onChange={setF('unit')} onFocus={fi} onBlur={fo}>
                {UNITS.map((u) => <option key={u}>{u}</option>)}
              </select>
            </FField>

            <FField label="Safety Stock" hint="Minimum quantity to keep on hand">
              <input style={inputStyle} type="number" value={form.safety_stock} onChange={setF('safety_stock')}
                placeholder="5000" onFocus={fi} onBlur={fo} />
            </FField>

            <FField label="Avg. Monthly Usage">
              <input style={inputStyle} type="number" value={form.avg_monthly_usage} onChange={setF('avg_monthly_usage')}
                placeholder="50000" onFocus={fi} onBlur={fo} />
            </FField>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 18 }}>
            <button onClick={() => setShowForm(false)} style={{
              padding: '9px 18px', borderRadius: 8, border: '1.5px solid #E5E7EB',
              background: 'white', color: '#374151', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            }}>Cancel</button>
            <button onClick={handleSave} disabled={saving} style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '9px 18px', borderRadius: 8, border: 'none',
              background: '#2563EB', color: 'white', fontSize: 13, fontWeight: 600,
              cursor: saving ? 'wait' : 'pointer',
            }}>
              {saving && <Loader size={12} />}
              {saving ? 'Saving…' : editId ? 'Save Changes' : 'Add Component'}
            </button>
          </div>
        </div>
      )}

      {!showForm && (
        <button onClick={openAdd} style={{
          display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '12px 16px',
          border: '2px dashed #DBEAFE', borderRadius: 10, background: '#F8FAFF', color: '#2563EB',
          fontSize: 13, fontWeight: 600, cursor: 'pointer', marginBottom: 24,
        }}>
          <Plus size={16} />Add Component
        </button>
      )}

      <NavRow onBack={onBack} onNext={onNext} />
    </div>
  );
}

function FilterPill({ active, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      padding: '5px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: 'pointer',
      border: active ? 'none' : '1.5px solid #E5E7EB',
      background: active ? '#2563EB' : 'white',
      color: active ? 'white' : '#6B7280', transition: 'all 0.15s',
    }}>{children}</button>
  );
}

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

function IBtn({ onClick, col, bg, disabled, children }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      width: 26, height: 26, borderRadius: 6, border: 'none', background: bg, color: col,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      cursor: disabled ? 'wait' : 'pointer', opacity: disabled ? 0.6 : 1,
    }}>{children}</button>
  );
}

function NavRow({ onBack, onNext }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
      <button onClick={onBack} style={{
        padding: '10px 20px', borderRadius: 8, border: '1.5px solid #E5E7EB',
        background: 'white', color: '#374151', fontSize: 13, fontWeight: 600, cursor: 'pointer',
      }}>← Back</button>
      <button onClick={onNext} style={{
        padding: '11px 26px', borderRadius: 10, border: 'none',
        background: 'linear-gradient(135deg, #2563EB, #1D4ED8)',
        color: 'white', fontSize: 14, fontWeight: 700, cursor: 'pointer',
        boxShadow: '0 4px 14px rgba(37,99,235,0.3)',
      }}>Review Setup →</button>
    </div>
  );
}
