/**
 * Step3Warehouses.jsx — Add / Edit / Delete warehouses (Setup Wizard, Step 3).
 * Mirrors the pattern of Step2Factories.
 */

import { useState, useEffect } from 'react';
import { Warehouse, Plus, Pencil, Trash2, MapPin, Loader, X, AlertCircle, Thermometer } from 'lucide-react';
import { useSetupStore } from '../../store/setupStore';
import {
  listWarehouses, createWarehouse, updateWarehouse, deleteWarehouse,
} from '../../services/manufacturerApi';

const STATUSES = ['Operational', 'Under Construction', 'Maintenance', 'Idle', 'Closed'];

const inputStyle = {
  width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8,
  padding: '9px 12px', fontSize: 13.5, outline: 'none',
  background: 'white', color: '#111827', transition: 'border-color 0.15s',
  boxSizing: 'border-box',
};
const fi = (e) => (e.target.style.borderColor = '#2563EB');
const fo = (e) => (e.target.style.borderColor = '#E5E7EB');

const EMPTY = {
  warehouse_name: '', warehouse_code: '', country: '',
  state: '', city: '', address: '', latitude: '', longitude: '',
  storage_capacity: '', operating_status: 'Operational',
  temp_controlled: false, warehouse_manager: '', contact_number: '',
};

export default function Step3Warehouses({ onNext, onBack }) {
  const { warehouses, setWarehouses, addWarehouse, updateWarehouse: storeUpd, removeWarehouse } = useSetupStore();
  const [loading,  setLoading]  = useState(true);
  const [saving,   setSaving]   = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editId,   setEditId]   = useState(null);
  const [form,     setForm]     = useState(EMPTY);
  const [errors,   setErrors]   = useState({});
  const [apiErr,   setApiErr]   = useState('');

  useEffect(() => {
    listWarehouses()
      .then((d) => setWarehouses(d || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const setF = (k) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((p) => ({ ...p, [k]: v }));
    if (errors[k]) setErrors((p) => ({ ...p, [k]: '' }));
  };

  function openAdd() { setForm(EMPTY); setEditId(null); setErrors({}); setApiErr(''); setShowForm(true); }

  function openEdit(wh) {
    setForm({
      warehouse_name:    wh.warehouse_name    || '',
      warehouse_code:    wh.warehouse_code    || '',
      country:           wh.country           || '',
      state:             wh.state             || '',
      city:              wh.city              || '',
      address:           wh.address           || '',
      latitude:          wh.latitude  != null ? String(wh.latitude)  : '',
      longitude:         wh.longitude != null ? String(wh.longitude) : '',
      storage_capacity:  wh.storage_capacity  || '',
      operating_status:  wh.operating_status  || 'Operational',
      temp_controlled:   wh.temp_controlled   ?? false,
      warehouse_manager: wh.warehouse_manager || '',
      contact_number:    wh.contact_number    || '',
    });
    setEditId(wh.id); setErrors({}); setApiErr(''); setShowForm(true);
  }

  function validate() {
    const e = {};
    if (!form.warehouse_name.trim()) e.warehouse_name = 'Name required';
    if (!form.warehouse_code.trim()) e.warehouse_code = 'Code required';
    if (!form.country.trim())        e.country = 'Country required';
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
        const updated = await updateWarehouse(editId, payload);
        storeUpd(editId, updated);
      } else {
        const created = await createWarehouse(payload);
        addWarehouse(created);
      }
      setShowForm(false);
    } catch (e) { setApiErr(e.message); }
    finally { setSaving(false); }
  }

  async function handleDelete(id) {
    setDeleting(id);
    try { await deleteWarehouse(id); removeWarehouse(id); }
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
          <Warehouse size={13} color="#2563EB" />
          <span style={{ fontSize: 12, fontWeight: 600, color: '#2563EB' }}>Step 3 of 7</span>
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#111827', marginBottom: 6 }}>Warehouses</h1>
        <p style={{ fontSize: 14, color: '#6B7280' }}>
          Add your storage and distribution facilities.
        </p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#9CA3AF' }}>
          <Loader size={20} style={{ animation: 'spin 1s linear infinite' }} />
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
          {warehouses.length === 0 && !showForm && (
            <div style={{
              border: '2px dashed #E5E7EB', borderRadius: 12, padding: 32,
              textAlign: 'center', color: '#9CA3AF',
            }}>
              <Warehouse size={28} color="#D1D5DB" style={{ margin: '0 auto 10px' }} />
              <p style={{ fontSize: 14, fontWeight: 600 }}>No warehouses added yet</p>
              <p style={{ fontSize: 12, marginTop: 4 }}>Click "Add Warehouse" to begin.</p>
            </div>
          )}

          {warehouses.map((wh) => (
            <div key={wh.id} style={{
              background: 'white', border: '1px solid #E5E7EB', borderRadius: 12,
              padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16,
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 10,
                background: 'linear-gradient(135deg, #EFF6FF, #DBEAFE)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}>
                <Warehouse size={18} color="#2563EB" />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>
                  {wh.warehouse_name}
                  <span style={{
                    marginLeft: 8, fontSize: 11, background: '#F3F4F6',
                    borderRadius: 6, padding: '2px 7px', color: '#6B7280', fontWeight: 500,
                  }}>{wh.warehouse_code}</span>
                  {wh.temp_controlled && (
                    <span style={{
                      marginLeft: 6, fontSize: 10, background: '#EFF6FF',
                      borderRadius: 6, padding: '2px 7px', color: '#2563EB', fontWeight: 600,
                    }}>
                      <Thermometer size={9} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                      Temp Controlled
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 12, color: '#6B7280', marginTop: 3 }}>
                  <MapPin size={10} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                  {[wh.city, wh.country].filter(Boolean).join(', ')} · {wh.storage_capacity || '—'} · {' '}
                  <span style={{ color: wh.operating_status === 'Operational' ? '#10B981' : '#F59E0B', fontWeight: 600 }}>
                    {wh.operating_status}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <IBtn onClick={() => openEdit(wh)} c="#2563EB" bg="#EFF6FF"><Pencil size={13} /></IBtn>
                <IBtn onClick={() => handleDelete(wh.id)} c="#EF4444" bg="#FEF2F2" disabled={deleting === wh.id}>
                  {deleting === wh.id ? <Loader size={13} /> : <Trash2 size={13} />}
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
              {editId ? 'Edit Warehouse' : 'New Warehouse'}
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
            {[
              ['Warehouse Name', 'warehouse_name', 'Central Distribution Hub', true],
              ['Warehouse Code', 'warehouse_code', 'WH-01', true],
              ['Country',        'country',        'India', true],
              ['State',          'state',          'Karnataka'],
              ['City',           'city',           'Bengaluru'],
              ['Storage Capacity','storage_capacity','50,000 sq ft'],
              ['Latitude',       'latitude',       '12.9716'],
              ['Longitude',      'longitude',      '77.5946'],
              ['Warehouse Manager','warehouse_manager','Priya Sharma'],
              ['Contact Number', 'contact_number', '+91 98765 43210'],
            ].map(([label, key, ph, req]) => (
              <FField key={key} label={label} required={req} err={errors[key]}>
                <input style={inputStyle} value={form[key]} onChange={setF(key)}
                  placeholder={ph} onFocus={fi} onBlur={fo} />
              </FField>
            ))}

            <FField label="Operating Status">
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={form.operating_status}
                onChange={setF('operating_status')} onFocus={fi} onBlur={fo}>
                {STATUSES.map((s) => <option key={s}>{s}</option>)}
              </select>
            </FField>

            <FField label="Temperature Controlled">
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginTop: 2 }}>
                <input type="checkbox" checked={form.temp_controlled} onChange={setF('temp_controlled')}
                  style={{ width: 16, height: 16, accentColor: '#2563EB', cursor: 'pointer' }} />
                <span style={{ fontSize: 13, color: '#374151' }}>Yes, this warehouse is temperature-controlled</span>
              </label>
            </FField>
          </div>

          <div style={{ marginTop: 12 }}>
            <FField label="Address">
              <input style={inputStyle} value={form.address} onChange={setF('address')}
                placeholder="Warehouse No. 5, KIADB Industrial Area" onFocus={fi} onBlur={fo} />
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
              {saving ? 'Saving…' : editId ? 'Save Changes' : 'Add Warehouse'}
            </button>
          </div>
        </div>
      )}

      {!showForm && (
        <button onClick={openAdd} style={{
          display: 'flex', alignItems: 'center', gap: 8,
          width: '100%', padding: '12px 16px',
          border: '2px dashed #DBEAFE', borderRadius: 10,
          background: '#F8FAFF', color: '#2563EB',
          fontSize: 13, fontWeight: 600, cursor: 'pointer', marginBottom: 24,
        }}>
          <Plus size={16} />Add Warehouse
        </button>
      )}

      <NavRow onBack={onBack} onNext={onNext} />
    </div>
  );
}

function FField({ label, required, err, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <label style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}{required && <span style={{ color: '#EF4444', marginLeft: 2 }}>*</span>}
      </label>
      {children}
      {err && <span style={{ fontSize: 10.5, color: '#EF4444' }}>{err}</span>}
    </div>
  );
}

function IBtn({ onClick, c, bg, disabled, children }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      width: 30, height: 30, borderRadius: 7, border: 'none',
      background: bg, color: c, display: 'flex', alignItems: 'center', justifyContent: 'center',
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
      }}>Continue →</button>
    </div>
  );
}
