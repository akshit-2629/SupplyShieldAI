import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Truck, Plus, Search, X, MapPin, Package, Calendar, ChevronRight,
  CheckCircle2, Clock, AlertTriangle, Circle, Trash2, Edit3
} from 'lucide-react';
import PageHeader from '../../components/supplier/shared/PageHeader';
import StatusBadge from '../../components/supplier/shared/StatusBadge';
import DataTable from '../../components/supplier/shared/DataTable';
import EmptyState from '../../components/supplier/shared/EmptyState';
import {
  getShipments, createShipment, updateShipmentStatus, deleteShipment
} from '../../services/supplierApi';

const STATUSES = ['All', 'PREPARING', 'IN_TRANSIT', 'CUSTOMS', 'DELIVERED', 'DELAYED', 'CANCELLED'];
const CARRIERS = ['FedEx', 'DHL', 'UPS', 'Maersk', 'Hapag-Lloyd', 'Other'];

const COLUMNS = [
  { key: 'id', label: 'Shipment ID', sortable: true, render: (v) => <span style={{ fontFamily: 'monospace', fontSize: 12, fontWeight: 600, color: '#2563EB' }}>{v || '—'}</span> },
  { key: 'destination', label: 'Destination', sortable: true, render: (v) => v ? <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><MapPin size={12} color="#9CA3AF" />{v}</div> : '—' },
  { key: 'carrier', label: 'Carrier', sortable: true },
  { key: 'dispatchDate', label: 'Dispatch', sortable: true, render: (v) => v ? new Date(v).toLocaleDateString() : '—' },
  { key: 'eta', label: 'ETA', sortable: true, render: (v) => v ? new Date(v).toLocaleDateString() : '—' },
  { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v?.toLowerCase().replace(' ', '_')} label={v} /> },
];

function Timeline({ events = [] }) {
  const defaults = [
    { label: 'Order Placed', status: 'done', time: null },
    { label: 'Dispatched', status: 'done', time: null },
    { label: 'In Transit', status: 'active', time: null },
    { label: 'Out for Delivery', status: 'pending', time: null },
    { label: 'Delivered', status: 'pending', time: null },
  ];
  const items = events.length
    ? events.map(e => ({ label: e.event, status: 'done', time: e.timestamp ? new Date(e.timestamp).toLocaleString() : null }))
    : defaults;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {items.map((item, i) => (
        <div key={i} style={{ display: 'flex', gap: 14 }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
            <div style={{ width: 28, height: 28, borderRadius: '50%', background: item.status === 'done' ? '#ECFDF5' : item.status === 'active' ? '#EFF6FF' : '#F3F4F6', border: `2px solid ${item.status === 'done' ? '#10B981' : item.status === 'active' ? '#2563EB' : '#E5E7EB'}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {item.status === 'done' ? <CheckCircle2 size={14} color="#10B981" /> : item.status === 'active' ? <Clock size={14} color="#2563EB" /> : <Circle size={10} color="#D1D5DB" />}
            </div>
            {i < items.length - 1 && <div style={{ width: 2, flex: 1, minHeight: 24, background: item.status === 'done' ? '#10B981' : '#E5E7EB' }} />}
          </div>
          <div style={{ paddingBottom: i < items.length - 1 ? 20 : 0, paddingTop: 4 }}>
            <div style={{ fontSize: 13, fontWeight: item.status === 'active' ? 700 : 500, color: item.status === 'pending' ? '#9CA3AF' : '#111827' }}>{item.label}</div>
            {item.time && <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2 }}>{item.time}</div>}
          </div>
        </div>
      ))}
    </div>
  );
}

function ShipmentDetailPanel({ shipment, onClose, onRefresh }) {
  const [updating, setUpdating] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleStatusUpdate(newStatus) {
    setUpdating(true);
    try {
      await updateShipmentStatus(shipment.dbId, newStatus, `Status updated to ${newStatus}`);
      onRefresh();
      onClose();
    } catch (err) {
      alert(err.message || 'Status update failed');
    } finally {
      setUpdating(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm(`Are you sure you want to delete shipment ${shipment.id}?`)) return;
    setDeleting(true);
    try {
      await deleteShipment(shipment.dbId);
      onRefresh();
      onClose();
    } catch (err) {
      alert(err.message || 'Delete failed');
    } finally {
      setDeleting(false);
    }
  }

  return (
    <motion.div initial={{ opacity: 0, x: 32 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 32 }}
      style={{ position: 'fixed', right: 0, top: 0, bottom: 0, width: 380, background: 'white', boxShadow: '-4px 0 40px rgba(0,0,0,0.12)', zIndex: 60, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '18px 20px', borderBottom: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, background: 'white' }}>
        <h3 style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>Shipment Details</h3>
        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}><X size={18} /></button>
      </div>
      <div style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Truck size={20} color="#2563EB" />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>{shipment.id || 'SHP-000001'}</div>
            <StatusBadge status={shipment.status?.toLowerCase().replace(' ', '_')} label={shipment.status || 'PREPARING'} />
          </div>
        </div>

        {[
          { label: 'Destination', value: shipment.destination || '—', icon: MapPin },
          { label: 'Carrier', value: shipment.carrier || '—', icon: Truck },
          { label: 'Dispatch Date', value: shipment.dispatchDate ? new Date(shipment.dispatchDate).toLocaleDateString() : '—', icon: Calendar },
          { label: 'ETA', value: shipment.eta ? new Date(shipment.eta).toLocaleDateString() : '—', icon: Calendar },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 0', borderBottom: '1px solid #F9FAFB' }}>
            <Icon size={14} color="#9CA3AF" style={{ flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: '#9CA3AF', marginBottom: 2 }}>{label}</div>
              <div style={{ fontSize: 13.5, fontWeight: 600, color: '#111827' }}>{value}</div>
            </div>
          </div>
        ))}

        {/* Update Status Actions */}
        <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid #F3F4F6' }}>
          <label style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>
            Update Shipment Status
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {['PREPARING', 'IN_TRANSIT', 'CUSTOMS', 'DELIVERED', 'DELAYED', 'CANCELLED'].map((st) => (
              <button key={st} disabled={updating} onClick={() => handleStatusUpdate(st)}
                style={{
                  padding: '5px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer',
                  border: '1px solid',
                  borderColor: shipment.status === st ? '#2563EB' : '#E5E7EB',
                  background: shipment.status === st ? '#EFF6FF' : 'white',
                  color: shipment.status === st ? '#2563EB' : '#374151',
                }}>
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 24 }}>
          <h4 style={{ fontSize: 13, fontWeight: 700, color: '#111827', marginBottom: 16 }}>Shipment Timeline</h4>
          <Timeline events={shipment.raw?.timeline || []} />
        </div>

        {/* Delete Button */}
        <div style={{ marginTop: 30, paddingTop: 16, borderTop: '1px solid #F3F4F6' }}>
          <button onClick={handleDelete} disabled={deleting}
            style={{
              width: '100%', padding: '9px 16px', borderRadius: 8, border: '1px solid #FCA5A5',
              background: '#FEF2F2', color: '#DC2626', fontSize: 13, fontWeight: 600, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8
            }}>
            <Trash2 size={14} /> {deleting ? 'Deleting…' : 'Delete Shipment'}
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function NewShipmentModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ destination: '', carrier: '', dispatchDate: '', eta: '', notes: '' });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm((p) => ({ ...p, [k]: e.target.value }));
  const inputSt = { width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '9px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box' };
  const labelSt = { fontSize: 11, fontWeight: 600, color: '#6B7280', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' };

  async function handleCreate() {
    if (!form.destination?.trim()) { alert('Destination is required'); return; }
    setSaving(true);
    try {
      const payload = {
        shipment_number: `SHP-${Date.now().toString().slice(-6)}`,
        carrier_name: form.carrier || 'Standard Carrier',
        destination_city: form.destination,
        destination_country: form.destination,
        shipped_at: form.dispatchDate ? new Date(form.dispatchDate).toISOString() : null,
        estimated_arrival: form.eta ? new Date(form.eta).toISOString() : null,
        notes: form.notes || '',
        status: 'PREPARING',
      };
      await createShipment(payload);
      onCreated();
    } catch (err) {
      console.error('Create shipment error:', err);
      alert(err.message || 'Failed to create shipment');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.25)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 20 }}>
      <motion.div initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }}
        style={{ background: 'white', borderRadius: 16, width: '100%', maxWidth: 480, overflow: 'hidden', boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}>
        <div style={{ padding: '18px 24px', borderBottom: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>Create Shipment</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}><X size={18} /></button>
        </div>
        <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div><label style={labelSt}>Destination *</label><input style={inputSt} value={form.destination} onChange={set('destination')} placeholder="City, Country" onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} /></div>
          <div><label style={labelSt}>Carrier</label>
            <select style={{ ...inputSt, cursor: 'pointer' }} value={form.carrier} onChange={set('carrier')}>
              <option value="">Select carrier…</option>
              {CARRIERS.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div><label style={labelSt}>Dispatch Date</label><input type="date" style={inputSt} value={form.dispatchDate} onChange={set('dispatchDate')} onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} /></div>
            <div><label style={labelSt}>ETA</label><input type="date" style={inputSt} value={form.eta} onChange={set('eta')} onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} /></div>
          </div>
          <div><label style={labelSt}>Notes</label><textarea style={{ ...inputSt, resize: 'vertical' }} rows={3} value={form.notes} onChange={set('notes')} placeholder="Cargo description, special instructions…" onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} /></div>
        </div>
        <div style={{ padding: '14px 24px', borderTop: '1px solid #F3F4F6', display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '8px 18px', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 13, background: 'white', color: '#374151', cursor: 'pointer', fontWeight: 600 }}>Cancel</button>
          <button onClick={handleCreate} disabled={saving} style={{ padding: '8px 20px', border: 'none', borderRadius: 8, fontSize: 13, background: '#2563EB', color: 'white', cursor: 'pointer', fontWeight: 700, opacity: saving ? 0.7 : 1 }}>
            {saving ? 'Creating…' : 'Create Shipment'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

export default function ShipmentManagement() {
  const [statusFilter, setStatusFilter] = useState('All');
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getShipments();
      const items = Array.isArray(res) ? res : (res?.items || res?.data || []);
      setShipments(items.map(s => ({
        id: s.shipment_number || s.id,
        dbId: s.id,
        destination: s.destination_city || s.destination_country || '',
        carrier: s.carrier_name || '',
        dispatchDate: s.shipped_at || s.created_at,
        eta: s.estimated_arrival,
        status: s.status ? s.status.replace(/_/g, ' ') : 'PREPARING',
        raw: s
      })));
    } catch (err) {
      console.error('Failed to load shipments:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = statusFilter === 'All'
    ? shipments
    : shipments.filter((s) => s.status?.toUpperCase() === statusFilter?.replace(' ', '_')?.toUpperCase());

  return (
    <div>
      <PageHeader
        title="Shipment Management"
        description="Track all your outbound shipments, delivery status, and carrier information"
        actions={
          <button onClick={() => setShowModal(true)}
            style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '9px 18px', border: 'none', borderRadius: 9, fontSize: 13.5, fontWeight: 700, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', color: 'white', cursor: 'pointer', boxShadow: '0 2px 10px rgba(37,99,235,0.3)' }}>
            <Plus size={15} /> New Shipment
          </button>
        }
      />

      {/* Status tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, overflowX: 'auto', paddingBottom: 4 }}>
        {STATUSES.map((s) => (
          <button key={s} onClick={() => setStatusFilter(s)}
            style={{ padding: '7px 16px', borderRadius: 8, border: `1.5px solid ${statusFilter === s ? '#2563EB' : '#E5E7EB'}`, background: statusFilter === s ? '#EFF6FF' : 'white', color: statusFilter === s ? '#2563EB' : '#6B7280', fontSize: 13, fontWeight: statusFilter === s ? 700 : 400, cursor: 'pointer', whiteSpace: 'nowrap', transition: 'all 0.15s' }}>
            {s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="card" style={{ padding: '20px 24px' }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: '#6B7280' }}>Loading shipments...</div>
        ) : filtered.length === 0 ? (
          <EmptyState
            type="package"
            title="No shipments found"
            description="Create your first shipment to start tracking orders and deliveries."
            actionLabel="Create Shipment"
            onAction={() => setShowModal(true)}
          />
        ) : (
          <DataTable
            columns={[...COLUMNS, {
              key: '_detail', label: '', render: (_, row) => (
                <button onClick={() => setSelected(row)} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#2563EB', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>
                  Details <ChevronRight size={13} />
                </button>
              )
            }]}
            data={filtered}
            searchable
            onRowClick={setSelected}
          />
        )}
      </div>

      {/* Detail slide-in */}
      <AnimatePresence>
        {selected && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSelected(null)}
              style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.15)', zIndex: 59 }} />
            <ShipmentDetailPanel shipment={selected} onClose={() => setSelected(null)} onRefresh={load} />
          </>
        )}
      </AnimatePresence>

      {showModal && <NewShipmentModal onClose={() => setShowModal(false)} onCreated={() => { setShowModal(false); load(); }} />}
    </div>
  );
}
