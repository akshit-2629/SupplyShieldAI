import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Package, Plus, Search, Filter, AlertTriangle, TrendingDown, Edit3, Trash2, Save, X, Boxes, RefreshCw } from 'lucide-react';
import PageHeader from '../../components/supplier/shared/PageHeader';
import StatusBadge from '../../components/supplier/shared/StatusBadge';
import DataTable from '../../components/supplier/shared/DataTable';
import EmptyState from '../../components/supplier/shared/EmptyState';
import ConfirmDialog from '../../components/supplier/shared/ConfirmDialog';
import { ProgressBar } from '../../components/supplier/shared/ProgressRing';
import { createInventoryItem, updateInventoryItem, deleteInventoryItem, getInventoryItems, getWarehouseSummary } from '../../services/supplierApi';

const CATEGORIES = ['All', 'Raw Materials', 'Finished Goods', 'Safety Stock', 'Reserved', 'Critical Components'];

const COLUMNS = [
  { key: 'name', label: 'Item Name', sortable: true },
  { key: 'sku', label: 'SKU', sortable: true },
  { key: 'category', label: 'Category', sortable: true, render: (v) => <StatusBadge status="info" label={v} /> },
  { key: 'quantity', label: 'Quantity', sortable: true, render: (v, row) => (
    <div>
      <div style={{ fontWeight: 700, color: v <= row.safetyStock ? '#EF4444' : '#111827' }}>{v}</div>
      {v <= row.safetyStock && <div style={{ fontSize: 10, color: '#EF4444', display: 'flex', alignItems: 'center', gap: 3 }}><AlertTriangle size={10} /> Below safety stock</div>}
    </div>
  )},
  { key: 'safetyStock', label: 'Safety Stock', sortable: true },
  { key: 'unit', label: 'Unit' },
  { key: 'location', label: 'Warehouse' },
  { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
];

function ItemModal({ item, onClose, onSave }) {
  const [form, setForm] = useState(item || { name: '', sku: '', category: 'Raw Materials', quantity: 0, safetyStock: 0, unit: 'units', location: '', status: 'active' });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm((p) => ({ ...p, [k]: e.target.value }));

  async function handleSave() {
    if (!form.name?.trim()) { alert('Item name is required'); return; }
    if (!form.sku?.trim()) { alert('SKU is required'); return; }
    setSaving(true);
    try {
      const payload = {
        name: form.name.trim(),
        sku: form.sku.trim(),
        category: form.category || 'Raw Materials',
        unit: form.unit || 'units',
        quantity_on_hand: parseInt(form.quantity, 10) || 0,
        safety_stock_level: parseInt(form.safetyStock, 10) || 0,
        warehouse_location: form.location || '',
      };
      if (item?.id) {
        await updateInventoryItem(item.id, payload);
      } else {
        await createInventoryItem(payload);
      }
      onSave();
    } catch (err) {
      console.error('Failed to save inventory item:', err);
      alert(err.message || 'Failed to save inventory item');
    } finally {
      setSaving(false);
    }
  }

  const inputSt = { width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '9px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box' };
  const labelSt = { fontSize: 11, fontWeight: 600, color: '#6B7280', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.25)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 20 }}>
      <motion.div initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
        style={{ background: 'white', borderRadius: 16, width: '100%', maxWidth: 520, overflow: 'hidden', boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}>
        <div style={{ padding: '18px 24px', borderBottom: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>{item ? 'Edit Inventory Item' : 'Add Inventory Item'}</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}><X size={18} /></button>
        </div>
        <div style={{ padding: '20px 24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div style={{ gridColumn: 'span 2' }}>
            <label style={labelSt}>Item Name</label>
            <input style={inputSt} value={form.name} onChange={set('name')} placeholder="e.g. Steel Sheet 2mm" onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} />
          </div>
          <div><label style={labelSt}>SKU</label><input style={inputSt} value={form.sku} onChange={set('sku')} placeholder="SKU-00001" onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} /></div>
          <div>
            <label style={labelSt}>Category</label>
            <select style={{ ...inputSt, cursor: 'pointer' }} value={form.category} onChange={set('category')}>
              {CATEGORIES.slice(1).map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div><label style={labelSt}>Quantity</label><input type="number" style={inputSt} value={form.quantity} onChange={set('quantity')} onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} /></div>
          <div><label style={labelSt}>Safety Stock</label><input type="number" style={inputSt} value={form.safetyStock} onChange={set('safetyStock')} onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} /></div>
          <div><label style={labelSt}>Unit</label><input style={inputSt} value={form.unit} onChange={set('unit')} placeholder="units / kg / pcs" onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} /></div>
          <div><label style={labelSt}>Warehouse Location</label><input style={inputSt} value={form.location} onChange={set('location')} placeholder="Warehouse A / Bay 3" onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} /></div>
        </div>
        <div style={{ padding: '14px 24px', borderTop: '1px solid #F3F4F6', display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '8px 18px', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 13, background: 'white', color: '#374151', cursor: 'pointer', fontWeight: 600 }}>Cancel</button>
          <button onClick={handleSave} disabled={saving} style={{ padding: '8px 20px', border: 'none', borderRadius: 8, fontSize: 13, background: '#10B981', color: 'white', cursor: 'pointer', fontWeight: 700, opacity: saving ? 0.7 : 1 }}>
            <Save size={13} style={{ marginRight: 6, verticalAlign: 'middle' }} />{saving ? 'Saving…' : 'Save Item'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

export default function InventoryManagement() {
  const [activeTab, setActiveTab] = useState('All');
  const [modal, setModal] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: PAGE_SIZE };
      if (search) params.search = search;
      if (activeTab !== 'All') params.category = activeTab;
      const res = await getInventoryItems(params);
      const rawRows = Array.isArray(res) ? res : (res?.data || res?.items || []);
      setItems(rawRows.map(r => ({
        id: r.id, name: r.name, sku: r.sku,
        category: r.category || 'General',
        quantity: r.quantity_on_hand ?? 0,
        safetyStock: r.safety_stock_level ?? 0,
        unit: r.unit || 'units',
        location: r.warehouse_location || '',
        status: r.is_active ? 'active' : 'inactive',
        isCritical: r.is_critical_component,
        isLowStock: r.is_low_stock,
      })));
      setTotal(res?.total ?? rawRows.length);
    } catch (err) {
      console.error('Inventory load error:', err);
    } finally {
      setLoading(false);
    }
  }, [page, search, activeTab]);

  useEffect(() => { load(); }, [load]);

  const filtered = items;
  const lowStock = items.filter((i) => i.isLowStock);

  const [wsSummary, setWsSummary] = useState(null);

  // Warehouse summary from server (includes all-time counts, not just current page)
  useEffect(() => {
    getWarehouseSummary().then(r => setWsSummary(r)).catch(() => {});
  }, [items]); // re-fetch when items change

  // Derived KPIs: prefer server-side, fall back to computed
  const warehouseSummary = [
    { label: 'Total SKUs',       value: wsSummary?.total_items   ?? total,                                                color: '#2563EB' },
    { label: 'Low Stock Alerts', value: wsSummary?.low_stock_count ?? lowStock.length,                                    color: '#EF4444' },
    { label: 'Categories',       value: wsSummary?.category_count  ?? (CATEGORIES.length - 1),                           color: '#10B981' },
    { label: 'Warehouses',       value: wsSummary?.warehouse_count  ?? ([...new Set(items.map(i => i.location).filter(Boolean))].length || 1), color: '#F59E0B' },
  ];

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteInventoryItem(deleteTarget.id);
      setDeleteTarget(null);
      load();
    } catch (err) {
      console.error('Delete inventory item error:', err);
      alert(err.message || 'Failed to delete inventory item');
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Inventory Management"
        description="Track raw materials, finished goods, safety stock, and warehouse health"
        actions={
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <button onClick={load}
              style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '9px 14px', border: '1px solid #E5E7EB', borderRadius: 9, fontSize: 13, fontWeight: 600, background: 'white', color: '#374151', cursor: 'pointer' }}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
            </button>
            <button onClick={() => setModal('add')}
              style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '9px 18px', border: 'none', borderRadius: 9, fontSize: 13.5, fontWeight: 700, background: 'linear-gradient(135deg, #10B981, #059669)', color: 'white', cursor: 'pointer', boxShadow: '0 2px 10px rgba(16,185,129,0.3)' }}>
              <Plus size={15} /> Add Item
            </button>
          </div>
        }
      />

      {/* Low stock warning banner */}
      {lowStock.length > 0 && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 10, padding: '12px 16px', marginBottom: 20, fontSize: 13, color: '#DC2626' }}>
          <AlertTriangle size={16} />
          <strong>{lowStock.length} item{lowStock.length > 1 ? 's' : ''}</strong> below safety stock level. Review and restock as soon as possible.
        </motion.div>
      )}

      {/* Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 12, marginBottom: 24 }}>
        {warehouseSummary.map(({ label, value, color }) => (
          <div key={label} className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: 22, fontWeight: 800, color }}>{value}</div>
            <div style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Category Tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20, overflowX: 'auto', paddingBottom: 4 }}>
        {CATEGORIES.map((c) => (
          <button key={c} onClick={() => setActiveTab(c)}
            style={{ padding: '7px 16px', borderRadius: 8, border: `1.5px solid ${activeTab === c ? '#10B981' : '#E5E7EB'}`, background: activeTab === c ? '#ECFDF5' : 'white', color: activeTab === c ? '#059669' : '#6B7280', fontSize: 13, fontWeight: activeTab === c ? 700 : 400, cursor: 'pointer', whiteSpace: 'nowrap', transition: 'all 0.15s' }}>
            {c}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="card" style={{ padding: '20px 24px' }}>
        {loading ? (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#6B7280', fontSize: 13.5 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', border: '3px solid #E5E7EB', borderTopColor: '#10B981', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px' }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            Loading inventory items…
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            type="package"
            title="No inventory items yet"
            description="Start adding your raw materials, finished goods, and safety stock to track inventory health."
            actionLabel="Add First Item"
            onAction={() => setModal('add')}
          />
        ) : (
          <DataTable
            columns={[...COLUMNS, {
              key: 'actions', label: '', render: (_, row) => (
                <div style={{ display: 'flex', gap: 6 }}>
                  <button onClick={() => setModal(row)} style={{ padding: '4px 10px', border: '1px solid #E5E7EB', borderRadius: 5, fontSize: 12, background: 'white', cursor: 'pointer' }}><Edit3 size={12} /></button>
                  <button onClick={() => setDeleteTarget(row)} style={{ padding: '4px 10px', border: '1px solid #FCA5A5', borderRadius: 5, fontSize: 12, background: '#FEF2F2', cursor: 'pointer', color: '#EF4444' }}><Trash2 size={12} /></button>
                </div>
              )
            }]}
            data={filtered}
            searchable
            emptyTitle={`No ${activeTab} items`}
          />
        )}
      </div>

      {modal && <ItemModal item={modal === 'add' ? null : modal} onClose={() => setModal(null)} onSave={() => { setModal(null); load(); }} />}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Inventory Item"
        description={`Are you sure you want to remove "${deleteTarget?.name}" from inventory? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
