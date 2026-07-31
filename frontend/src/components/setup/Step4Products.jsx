/**
 * Step4Products.jsx — Define the products the manufacturer makes (Setup Wizard, Step 4).
 */

import { useState, useEffect } from 'react';
import { Package, Plus, Pencil, Trash2, Loader, X, AlertCircle } from 'lucide-react';
import { useSetupStore } from '../../store/setupStore';
import { listProducts, createProduct, updateProduct, deleteProduct } from '../../services/manufacturerApi';

const CATEGORIES = [
  'Consumer Electronics', 'Semiconductors', 'Industrial Electronics', 'Automotive Parts',
  'Medical Devices', 'Aerospace Components', 'Networking Equipment', 'Appliances', 'Other',
];

const STATUSES = ['Active', 'Development', 'Discontinued', 'On Hold'];

const inputStyle = {
  width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8,
  padding: '9px 12px', fontSize: 13.5, outline: 'none',
  background: 'white', color: '#111827', transition: 'border-color 0.15s', boxSizing: 'border-box',
};
const fi = (e) => (e.target.style.borderColor = '#2563EB');
const fo = (e) => (e.target.style.borderColor = '#E5E7EB');

const EMPTY = {
  product_name: '', sku: '', category: 'Consumer Electronics',
  model_number: '', description: '', production_volume: '', status: 'Active',
};

const STATUS_COLORS = {
  Active: '#10B981', Development: '#F59E0B', Discontinued: '#EF4444', 'On Hold': '#6B7280',
};

export default function Step4Products({ onNext, onBack }) {
  const { products, setProducts, addProduct, updateProduct: storeUpd, removeProduct } = useSetupStore();
  const [loading,  setLoading]  = useState(true);
  const [saving,   setSaving]   = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editId,   setEditId]   = useState(null);
  const [form,     setForm]     = useState(EMPTY);
  const [errors,   setErrors]   = useState({});
  const [apiErr,   setApiErr]   = useState('');

  useEffect(() => {
    listProducts()
      .then((d) => setProducts(d || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const setF = (k) => (e) => {
    setForm((p) => ({ ...p, [k]: e.target.value }));
    if (errors[k]) setErrors((p) => ({ ...p, [k]: '' }));
  };

  function openAdd() { setForm(EMPTY); setEditId(null); setErrors({}); setApiErr(''); setShowForm(true); }

  function openEdit(p) {
    setForm({
      product_name:      p.product_name      || '',
      sku:               p.sku               || '',
      category:          p.category          || 'Consumer Electronics',
      model_number:      p.model_number      || '',
      description:       p.description       || '',
      production_volume: p.production_volume != null ? String(p.production_volume) : '',
      status:            p.status            || 'Active',
    });
    setEditId(p.id); setErrors({}); setApiErr(''); setShowForm(true);
  }

  function validate() {
    const e = {};
    if (!form.product_name.trim()) e.product_name = 'Product name required';
    if (!form.sku.trim())          e.sku = 'SKU required';
    return e;
  }

  async function handleSave() {
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setSaving(true); setApiErr('');
    try {
      const payload = {
        ...form,
        production_volume: form.production_volume ? parseInt(form.production_volume, 10) : null,
      };
      if (editId) {
        const u = await updateProduct(editId, payload);
        storeUpd(editId, u);
      } else {
        const c = await createProduct(payload);
        addProduct(c);
      }
      setShowForm(false);
    } catch (e) { setApiErr(e.message); }
    finally { setSaving(false); }
  }

  async function handleDelete(id) {
    setDeleting(id);
    try { await deleteProduct(id); removeProduct(id); }
    catch (e) { setApiErr(e.message); }
    finally { setDeleting(null); }
  }

  return (
    <div style={{ maxWidth: 760, animation: 'slideUp 0.3s ease both' }}>
      <div style={{ marginBottom: 28 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: '#EFF6FF', border: '1px solid #DBEAFE',
          borderRadius: 20, padding: '4px 12px', marginBottom: 12,
        }}>
          <Package size={13} color="#2563EB" />
          <span style={{ fontSize: 12, fontWeight: 600, color: '#2563EB' }}>Step 4 of 7</span>
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#111827', marginBottom: 6 }}>Products</h1>
        <p style={{ fontSize: 14, color: '#6B7280' }}>
          Define every product you manufacture. Components are linked to products in the next step.
        </p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Loader size={20} style={{ animation: 'spin 1s linear infinite', color: '#9CA3AF' }} />
        </div>
      ) : (
        <>
          {products.length === 0 && !showForm ? (
            <div style={{
              border: '2px dashed #E5E7EB', borderRadius: 12, padding: 32,
              textAlign: 'center', color: '#9CA3AF', marginBottom: 16,
            }}>
              <Package size={28} color="#D1D5DB" style={{ margin: '0 auto 10px' }} />
              <p style={{ fontSize: 14, fontWeight: 600 }}>No products defined yet</p>
              <p style={{ fontSize: 12, marginTop: 4 }}>e.g. Smartphone X, Laptop Pro, Tablet Ultra</p>
            </div>
          ) : (
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))',
              gap: 12, marginBottom: 16,
            }}>
              {products.map((p) => (
                <div key={p.id} style={{
                  background: 'white', border: '1px solid #E5E7EB', borderRadius: 12,
                  padding: '16px 18px', position: 'relative',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: 10,
                      background: 'linear-gradient(135deg, #EFF6FF, #DBEAFE)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <Package size={16} color="#2563EB" />
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <IBtn onClick={() => openEdit(p)} c="#2563EB" bg="#EFF6FF"><Pencil size={11} /></IBtn>
                      <IBtn onClick={() => handleDelete(p.id)} c="#EF4444" bg="#FEF2F2" disabled={deleting === p.id}>
                        {deleting === p.id ? <Loader size={11} /> : <Trash2 size={11} />}
                      </IBtn>
                    </div>
                  </div>
                  <div style={{ marginTop: 12 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>{p.product_name}</div>
                    <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2 }}>{p.sku}</div>
                    <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                      <Tag color="#6B7280">{p.category}</Tag>
                      <Tag color={STATUS_COLORS[p.status] || '#6B7280'}>{p.status}</Tag>
                    </div>
                    {p.production_volume && (
                      <div style={{ fontSize: 11, color: '#6B7280', marginTop: 6 }}>
                        {p.production_volume.toLocaleString()} units/month
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Inline form */}
      {showForm && (
        <div style={{
          background: 'white', border: '1.5px solid #DBEAFE', borderRadius: 12,
          padding: 24, marginBottom: 16, animation: 'slideDown 0.2s ease both',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 18 }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>
              {editId ? 'Edit Product' : 'New Product'}
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
            <FField label="Product Name" required err={errors.product_name}>
              <input style={inputStyle} value={form.product_name} onChange={setF('product_name')}
                placeholder="Smartphone X" onFocus={fi} onBlur={fo} />
            </FField>
            <FField label="SKU" required err={errors.sku}>
              <input style={inputStyle} value={form.sku} onChange={setF('sku')}
                placeholder="SMTX-001" onFocus={fi} onBlur={fo} />
            </FField>
            <FField label="Category">
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={form.category}
                onChange={setF('category')} onFocus={fi} onBlur={fo}>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </FField>
            <FField label="Model Number">
              <input style={inputStyle} value={form.model_number} onChange={setF('model_number')}
                placeholder="AE-SMX-2024" onFocus={fi} onBlur={fo} />
            </FField>
            <FField label="Monthly Production Volume" hint="units per month">
              <input style={inputStyle} type="number" value={form.production_volume}
                onChange={setF('production_volume')} placeholder="50000" onFocus={fi} onBlur={fo} />
            </FField>
            <FField label="Status">
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={form.status}
                onChange={setF('status')} onFocus={fi} onBlur={fo}>
                {STATUSES.map((s) => <option key={s}>{s}</option>)}
              </select>
            </FField>
          </div>
          <div style={{ marginTop: 14 }}>
            <FField label="Description">
              <textarea style={{ ...inputStyle, resize: 'vertical' }} value={form.description}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                rows={2} placeholder="Flagship smartphone with OLED display and 108MP camera..."
                onFocus={fi} onBlur={fo} />
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
              {saving ? 'Saving…' : editId ? 'Save Changes' : 'Add Product'}
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
          <Plus size={16} />Add Product
        </button>
      )}

      <NavRow onBack={onBack} onNext={onNext} />
    </div>
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

function IBtn({ onClick, c, bg, disabled, children }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      width: 26, height: 26, borderRadius: 6, border: 'none', background: bg, color: c,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      cursor: disabled ? 'wait' : 'pointer', opacity: disabled ? 0.6 : 1,
    }}>{children}</button>
  );
}

function Tag({ color, children }) {
  return (
    <span style={{
      fontSize: 10, fontWeight: 600, color: 'white', background: color,
      borderRadius: 20, padding: '2px 7px',
    }}>{children}</span>
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
      }}>Continue →</button>
    </div>
  );
}
