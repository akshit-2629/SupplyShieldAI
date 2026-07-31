import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ClipboardCheck, Plus, Search, Filter, X, ChevronDown, Edit3, Trash2,
  AlertTriangle, CheckCircle, Clock, TrendingDown, FileText, History,
  Download, ChevronRight, BarChart3
} from 'lucide-react';
import {
  getQualityRecords, getQualityKpis, createQualityRecord,
  updateQualityRecord, deleteQualityRecord, getQualityHistory
} from '../../services/supplierApi';

// ── Severity badge ────────────────────────────────────────────────────────────
const SEV_COLORS = {
  MINOR:    { bg: '#F0FDF4', text: '#15803D', dot: '#22C55E' },
  MAJOR:    { bg: '#FFFBEB', text: '#B45309', dot: '#F59E0B' },
  CRITICAL: { bg: '#FEF2F2', text: '#B91C1C', dot: '#EF4444' },
};
const STATUS_COLORS = {
  OPEN:              { bg: '#EFF6FF', text: '#1D4ED8' },
  IN_REVIEW:         { bg: '#FEF9C3', text: '#854D0E' },
  CORRECTIVE_ACTION: { bg: '#FFF7ED', text: '#C2410C' },
  CLOSED:            { bg: '#F0FDF4', text: '#15803D' },
  ESCALATED:         { bg: '#FEF2F2', text: '#B91C1C' },
};

function SeverityBadge({ s }) {
  const c = SEV_COLORS[s] || SEV_COLORS.MINOR;
  return (
    <span style={{ background: c.bg, color: c.text, borderRadius: 99, padding: '2px 10px', fontSize: 11, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: c.dot, flexShrink: 0 }} />
      {s}
    </span>
  );
}

function StatusBadgeQ({ s }) {
  const c = STATUS_COLORS[s] || STATUS_COLORS.OPEN;
  return <span style={{ background: c.bg, color: c.text, borderRadius: 99, padding: '2px 10px', fontSize: 11, fontWeight: 700 }}>{s?.replace(/_/g, ' ')}</span>;
}

// ── KPI Card ─────────────────────────────────────────────────────────────────
function KpiCard({ label, value, icon: Icon, color, sub }) {
  return (
    <div style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 14, padding: '18px 20px', display: 'flex', alignItems: 'center', gap: 16, flex: 1, minWidth: 0 }}>
      <div style={{ width: 44, height: 44, borderRadius: 12, background: color + '18', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={20} color={color} />
      </div>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: 24, fontWeight: 800, color: '#111827' }}>{value ?? '—'}</div>
        <div style={{ fontSize: 12, color: '#6B7280', fontWeight: 500 }}>{label}</div>
        {sub && <div style={{ fontSize: 11, color: '#9CA3AF' }}>{sub}</div>}
      </div>
    </div>
  );
}

// ── Record Form (Create / Edit) ───────────────────────────────────────────────
const RECORD_TYPES = ['INSPECTION_REPORT','DEFECT_LOG','CORRECTIVE_ACTION','AUDIT_REPORT','CUSTOMER_COMPLAINT','INTERNAL_AUDIT','COMPLIANCE_CHECK','QUALITY_ALERT'];
const SEVERITIES   = ['MINOR','MAJOR','CRITICAL'];
const STATUSES     = ['OPEN','IN_REVIEW','CORRECTIVE_ACTION','CLOSED','ESCALATED'];
const inp = { width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '9px 12px', fontSize: 13, boxSizing: 'border-box', outline: 'none', transition: 'border-color 0.15s' };
const lbl = { fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 5 };

function QualityForm({ initial, onSave, onClose }) {
  const [form, setForm] = useState({
    title: '', record_type: 'INSPECTION_REPORT', severity: 'MINOR', status: 'OPEN',
    description: '', inspection_date: '', product_sku: '', product_name: '',
    batch_number: '', quantity_inspected: '', quantity_passed: '', quantity_failed: '',
    root_cause: '', corrective_action: '', standard_reference: '',
    customer_notified: false, regulatory_reportable: false,
    ...(initial || {}),
  });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    if (!form.title.trim()) { setErr('Title is required'); return; }
    setSaving(true); setErr('');
    try {
      const payload = { ...form };
      ['quantity_inspected','quantity_passed','quantity_failed'].forEach(k => {
        if (payload[k] !== '' && payload[k] !== null) payload[k] = Number(payload[k]);
        else delete payload[k];
      });
      await onSave(payload);
    } catch (e) { setErr(e.message || 'Save failed'); setSaving(false); }
  }

  return (
    <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'grid', gap: 14, gridTemplateColumns: '1fr 1fr' }}>
        <div style={{ gridColumn: 'span 2' }}>
          <label style={lbl}>Title *</label>
          <input style={inp} value={form.title} onChange={e => set('title', e.target.value)} placeholder="Brief description of the quality event" onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div>
          <label style={lbl}>Record Type</label>
          <select style={inp} value={form.record_type} onChange={e => set('record_type', e.target.value)}>
            {RECORD_TYPES.map(t => <option key={t}>{t.replace(/_/g,' ')}</option>)}
          </select>
        </div>
        <div>
          <label style={lbl}>Severity</label>
          <select style={{ ...inp, borderColor: SEV_COLORS[form.severity]?.dot }} value={form.severity} onChange={e => set('severity', e.target.value)}>
            {SEVERITIES.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label style={lbl}>Status</label>
          <select style={inp} value={form.status} onChange={e => set('status', e.target.value)}>
            {STATUSES.map(s => <option key={s}>{s.replace(/_/g,' ')}</option>)}
          </select>
        </div>
        <div>
          <label style={lbl}>Inspection Date</label>
          <input type="date" style={inp} value={form.inspection_date || ''} onChange={e => set('inspection_date', e.target.value)} />
        </div>
        <div>
          <label style={lbl}>Product SKU</label>
          <input style={inp} value={form.product_sku || ''} onChange={e => set('product_sku', e.target.value)} placeholder="e.g. IC-7805-TO220" onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div>
          <label style={lbl}>Product Name</label>
          <input style={inp} value={form.product_name || ''} onChange={e => set('product_name', e.target.value)} onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div>
          <label style={lbl}>Batch / Lot Number</label>
          <input style={inp} value={form.batch_number || ''} onChange={e => set('batch_number', e.target.value)} onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div>
          <label style={lbl}>Qty Inspected</label>
          <input type="number" style={inp} value={form.quantity_inspected || ''} onChange={e => set('quantity_inspected', e.target.value)} onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div>
          <label style={lbl}>Qty Passed</label>
          <input type="number" style={inp} value={form.quantity_passed || ''} onChange={e => set('quantity_passed', e.target.value)} onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div>
          <label style={lbl}>Qty Failed</label>
          <input type="number" style={inp} value={form.quantity_failed || ''} onChange={e => set('quantity_failed', e.target.value)} onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div style={{ gridColumn: 'span 2' }}>
          <label style={lbl}>Description</label>
          <textarea style={{ ...inp, resize: 'vertical', minHeight: 72 }} value={form.description || ''} onChange={e => set('description', e.target.value)} placeholder="Detailed description of the quality event…" onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div style={{ gridColumn: 'span 2' }}>
          <label style={lbl}>Root Cause Analysis</label>
          <textarea style={{ ...inp, resize: 'vertical', minHeight: 60 }} value={form.root_cause || ''} onChange={e => set('root_cause', e.target.value)} onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div style={{ gridColumn: 'span 2' }}>
          <label style={lbl}>Corrective Action</label>
          <textarea style={{ ...inp, resize: 'vertical', minHeight: 60 }} value={form.corrective_action || ''} onChange={e => set('corrective_action', e.target.value)} onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div>
          <label style={lbl}>Standard Reference</label>
          <input style={inp} value={form.standard_reference || ''} onChange={e => set('standard_reference', e.target.value)} placeholder="ISO 9001:2015 §8.7" onFocus={e=>e.target.style.borderColor='#10B981'} onBlur={e=>e.target.style.borderColor='#E5E7EB'} />
        </div>
        <div style={{ display: 'flex', gap: 20, alignItems: 'center', paddingTop: 18 }}>
          {[['customer_notified','Customer Notified'],['regulatory_reportable','Regulatory Reportable']].map(([k, label]) => (
            <label key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151', cursor: 'pointer' }}>
              <input type="checkbox" checked={!!form[k]} onChange={e => set(k, e.target.checked)}
                style={{ width: 15, height: 15, accentColor: '#10B981', cursor: 'pointer' }} />
              {label}
            </label>
          ))}
        </div>
      </div>
      {err && <div style={{ padding: '0 24px 12px', fontSize: 13, color: '#EF4444', fontWeight: 600 }}>{err}</div>}
      <div style={{ padding: '16px 24px', borderTop: '1px solid #F3F4F6', display: 'flex', gap: 12, justifyContent: 'flex-end', background: '#FAFAFA' }}>
        <button type="button" onClick={onClose} style={{ padding: '9px 18px', border: '1.5px solid #E5E7EB', borderRadius: 8, background: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer', color: '#374151' }}>Cancel</button>
        <button type="submit" disabled={saving} style={{ padding: '9px 22px', border: 'none', borderRadius: 8, background: saving ? '#D1FAE5' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', fontSize: 13, fontWeight: 700, cursor: saving ? 'default' : 'pointer' }}>
          {saving ? 'Saving…' : initial ? 'Update Record' : 'Create Record'}
        </button>
      </div>
    </form>
  );
}

// ── Slide-over Panel ─────────────────────────────────────────────────────────
function SlideOver({ open, onClose, title, width = 680, children }) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.25)', zIndex: 100 }} />
          <motion.div initial={{ x: width }} animate={{ x: 0 }} exit={{ x: width }}
            transition={{ type: 'spring', damping: 28, stiffness: 280 }}
            style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width, background: 'white', zIndex: 101, boxShadow: '-4px 0 40px rgba(0,0,0,0.12)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '18px 24px', borderBottom: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#FAFAFA' }}>
              <span style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>{title}</span>
              <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6B7280' }}><X size={18} /></button>
            </div>
            <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// ── History Panel ─────────────────────────────────────────────────────────────
function HistoryPanel({ recordId, onClose }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!recordId) return;
    getQualityHistory(recordId).then(res => {
      setHistory(Array.isArray(res) ? res : (res?.data ?? []));
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [recordId]);
  return (
    <div style={{ padding: 20, overflowY: 'auto', height: '100%' }}>
      {loading ? <div style={{ textAlign: 'center', color: '#9CA3AF', marginTop: 40 }}>Loading…</div>
        : history.length === 0 ? <div style={{ textAlign: 'center', color: '#9CA3AF', marginTop: 40 }}>No history yet</div>
        : history.map((h, i) => (
          <div key={i} style={{ borderLeft: '2px solid #D1FAE5', paddingLeft: 16, marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#374151' }}>Version {h.version}</span>
              <span style={{ fontSize: 11, color: '#9CA3AF' }}>{h.changed_at ? new Date(h.changed_at).toLocaleString() : ''}</span>
            </div>
            <div style={{ fontSize: 12, color: '#6B7280', marginBottom: 4 }}>{h.change_summary || 'Updated'}</div>
            {h.changed_by && <div style={{ fontSize: 11, color: '#10B981' }}>by {h.changed_by}</div>}
          </div>
        ))
      }
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function QualityManagement() {
  const [records, setRecords]  = useState([]);
  const [kpis, setKpis]        = useState({});
  const [loading, setLoading]  = useState(true);
  const [total, setTotal]      = useState(0);
  const [page, setPage]        = useState(1);

  // Filters
  const [search, setSearch]           = useState('');
  const [filterType, setFilterType]   = useState('');
  const [filterSev, setFilterSev]     = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  // Panels
  const [formOpen, setFormOpen]     = useState(false);
  const [editRecord, setEditRecord] = useState(null);
  const [histRecord, setHistRecord] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting]     = useState(false);

  const PAGE_SIZE = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: PAGE_SIZE };
      if (search)       params.search      = search;
      if (filterType)   params.record_type = filterType;
      if (filterSev)    params.severity    = filterSev;
      if (filterStatus) params.status      = filterStatus;
      const [recRes, kpiRes] = await Promise.allSettled([
        getQualityRecords(params), getQualityKpis()
      ]);
      if (recRes.status === 'fulfilled') {
        const d = recRes.value;
        const rows = Array.isArray(d) ? d : (d?.items ?? d?.data ?? []);
        setRecords(rows);
        setTotal(d?.total ?? rows.length);
      }
      if (kpiRes.status === 'fulfilled') {
        const k = kpiRes.value;
        setKpis(k?.data ?? k ?? {});
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [page, search, filterType, filterSev, filterStatus]);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(data) {
    await createQualityRecord(data);
    setFormOpen(false);
    load();
  }
  async function handleUpdate(data) {
    await updateQualityRecord(editRecord.id, data);
    setEditRecord(null);
    load();
  }
  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    await deleteQualityRecord(deleteTarget.id);
    setDeleting(false);
    setDeleteTarget(null);
    load();
  }

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: '#FEF3C7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ClipboardCheck size={20} color="#D97706" />
          </div>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', margin: 0 }}>Quality Management</h1>
            <p style={{ fontSize: 13, color: '#6B7280', margin: 0 }}>Inspection reports, defect logs &amp; corrective actions</p>
          </div>
        </div>
        <button onClick={() => setFormOpen(true)}
          style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', border: 'none', borderRadius: 10, background: 'linear-gradient(135deg, #10B981, #059669)', color: 'white', fontSize: 14, fontWeight: 700, cursor: 'pointer', boxShadow: '0 2px 8px rgba(16,185,129,0.3)' }}>
          <Plus size={16} /> New Record
        </button>
      </div>

      {/* KPIs */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 24, flexWrap: 'wrap' }}>
        <KpiCard label="Total Records" value={kpis.total ?? 0} icon={ClipboardCheck} color="#2563EB" />
        <KpiCard label="Open Issues" value={kpis.open ?? 0} icon={AlertTriangle} color="#EF4444" />
        <KpiCard label="Closed" value={kpis.closed ?? 0} icon={CheckCircle} color="#10B981" />
        <KpiCard label="Critical" value={kpis.critical ?? 0} icon={AlertTriangle} color="#DC2626" />
        <KpiCard label="Avg Defect Rate" value={kpis.avg_defect_rate_pct != null ? `${kpis.avg_defect_rate_pct}%` : '—'} icon={TrendingDown} color="#F59E0B" />
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 18, flexWrap: 'wrap', background: 'white', borderRadius: 12, padding: '14px 18px', border: '1px solid #E5E7EB' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
          <Search size={14} color="#9CA3AF" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
          <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Search records…"
            style={{ width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '8px 12px 8px 34px', fontSize: 13, outline: 'none', boxSizing: 'border-box' }} />
        </div>
        {[
          { label: 'Type', val: filterType, set: setFilterType, opts: RECORD_TYPES },
          { label: 'Severity', val: filterSev, set: setFilterSev, opts: SEVERITIES },
          { label: 'Status', val: filterStatus, set: setFilterStatus, opts: STATUSES },
        ].map(({ label: l, val, set: s, opts }) => (
          <select key={l} value={val} onChange={e => { s(e.target.value); setPage(1); }}
            style={{ border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '8px 12px', fontSize: 13, outline: 'none', background: 'white', color: '#374151', minWidth: 130 }}>
            <option value="">All {l}s</option>
            {opts.map(o => <option key={o} value={o}>{o.replace(/_/g,' ')}</option>)}
          </select>
        ))}
      </div>

      {/* Table */}
      <div style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 14, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 60, textAlign: 'center', color: '#9CA3AF' }}>
            <div style={{ width: 36, height: 36, border: '3px solid #E5E7EB', borderTopColor: '#10B981', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px' }} />
            <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
            Loading records…
          </div>
        ) : records.length === 0 ? (
          <div style={{ padding: 60, textAlign: 'center' }}>
            <ClipboardCheck size={44} color="#E5E7EB" style={{ marginBottom: 12 }} />
            <div style={{ fontSize: 16, fontWeight: 700, color: '#374151', marginBottom: 6 }}>No quality records yet</div>
            <div style={{ fontSize: 13, color: '#9CA3AF', marginBottom: 18 }}>Create your first inspection report or defect log</div>
            <button onClick={() => setFormOpen(true)} style={{ padding: '9px 20px', border: 'none', borderRadius: 9, background: 'linear-gradient(135deg, #10B981, #059669)', color: 'white', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>+ New Record</button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#F9FAFB', borderBottom: '1px solid #E5E7EB' }}>
                  {['Record #','Type','Title','Severity','Status','Product','Defect Rate','Date','Actions'].map(h => (
                    <th key={h} style={{ padding: '11px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {records.map((r, i) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid #F3F4F6', background: i % 2 === 0 ? 'white' : '#FAFAFA' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#F0FDF4'}
                    onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'white' : '#FAFAFA'}>
                    <td style={{ padding: '11px 14px', fontWeight: 700, color: '#111827', whiteSpace: 'nowrap' }}>{r.record_number}</td>
                    <td style={{ padding: '11px 14px', color: '#6B7280', whiteSpace: 'nowrap' }}>{(r.record_type || '').replace(/_/g,' ')}</td>
                    <td style={{ padding: '11px 14px', color: '#111827', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.title}>{r.title}</td>
                    <td style={{ padding: '11px 14px' }}><SeverityBadge s={r.severity} /></td>
                    <td style={{ padding: '11px 14px' }}><StatusBadgeQ s={r.status} /></td>
                    <td style={{ padding: '11px 14px', color: '#6B7280' }}>{r.product_sku || r.product_name || '—'}</td>
                    <td style={{ padding: '11px 14px', color: r.defect_rate_pct > 5 ? '#EF4444' : '#374151', fontWeight: r.defect_rate_pct > 5 ? 700 : 400 }}>
                      {r.defect_rate_pct != null ? `${r.defect_rate_pct}%` : '—'}
                    </td>
                    <td style={{ padding: '11px 14px', color: '#6B7280', whiteSpace: 'nowrap' }}>{r.inspection_date || '—'}</td>
                    <td style={{ padding: '11px 14px' }}>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button onClick={() => setHistRecord(r.id)} title="History" style={{ background: '#F0F9FF', border: 'none', borderRadius: 6, padding: '5px 7px', cursor: 'pointer', color: '#2563EB' }}><History size={13} /></button>
                        <button onClick={() => setEditRecord(r)} title="Edit" style={{ background: '#ECFDF5', border: 'none', borderRadius: 6, padding: '5px 7px', cursor: 'pointer', color: '#059669' }}><Edit3 size={13} /></button>
                        <button onClick={() => setDeleteTarget(r)} title="Delete" style={{ background: '#FEF2F2', border: 'none', borderRadius: 6, padding: '5px 7px', cursor: 'pointer', color: '#EF4444' }}><Trash2 size={13} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {total > PAGE_SIZE && (
          <div style={{ padding: '12px 18px', borderTop: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 12, color: '#9CA3AF' }}>Showing {((page-1)*PAGE_SIZE)+1}–{Math.min(page*PAGE_SIZE, total)} of {total}</span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={() => setPage(p=>Math.max(p-1,1))} disabled={page===1}
                style={{ padding: '6px 12px', border: '1px solid #E5E7EB', borderRadius: 7, background: 'white', cursor: page===1 ? 'default' : 'pointer', opacity: page===1 ? 0.4 : 1, fontSize: 13 }}>← Prev</button>
              <button onClick={() => setPage(p=>p+1)} disabled={page*PAGE_SIZE>=total}
                style={{ padding: '6px 12px', border: '1px solid #E5E7EB', borderRadius: 7, background: 'white', cursor: page*PAGE_SIZE>=total ? 'default' : 'pointer', opacity: page*PAGE_SIZE>=total ? 0.4 : 1, fontSize: 13 }}>Next →</button>
            </div>
          </div>
        )}
      </div>

      {/* Create Panel */}
      <SlideOver open={formOpen} onClose={() => setFormOpen(false)} title="New Quality Record">
        <QualityForm onSave={handleCreate} onClose={() => setFormOpen(false)} />
      </SlideOver>

      {/* Edit Panel */}
      <SlideOver open={!!editRecord} onClose={() => setEditRecord(null)} title="Edit Quality Record">
        {editRecord && <QualityForm initial={editRecord} onSave={handleUpdate} onClose={() => setEditRecord(null)} />}
      </SlideOver>

      {/* History Panel */}
      <SlideOver open={!!histRecord} onClose={() => setHistRecord(null)} title="Version History" width={500}>
        {histRecord && <HistoryPanel recordId={histRecord} onClose={() => setHistRecord(null)} />}
      </SlideOver>

      {/* Delete Confirm */}
      <AnimatePresence>
        {deleteTarget && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }}
              style={{ background: 'white', borderRadius: 16, padding: 28, maxWidth: 400, width: '90%', boxShadow: '0 8px 40px rgba(0,0,0,0.15)' }}>
              <div style={{ fontSize: 16, fontWeight: 800, color: '#111827', marginBottom: 10 }}>Delete Quality Record?</div>
              <div style={{ fontSize: 13, color: '#6B7280', marginBottom: 22 }}>
                Are you sure you want to delete <strong>{deleteTarget.record_number}</strong>? This action is irreversible.
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button onClick={() => setDeleteTarget(null)} style={{ padding: '9px 18px', border: '1.5px solid #E5E7EB', borderRadius: 8, background: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Cancel</button>
                <button onClick={handleDelete} disabled={deleting} style={{ padding: '9px 18px', border: 'none', borderRadius: 8, background: '#EF4444', color: 'white', fontSize: 13, fontWeight: 700, cursor: deleting ? 'default' : 'pointer' }}>
                  {deleting ? 'Deleting…' : 'Delete'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
