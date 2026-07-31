import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Upload, Plus, Search, Filter, Trash2, X, Download,
  Eye, AlertTriangle, History, FolderOpen, Tag, Shield, Clock,
  CheckCircle, RefreshCw, FileCheck, Calendar, ExternalLink
} from 'lucide-react';
import {
  getDocuments, uploadDocument, updateDocument,
  deleteDocument, getDocumentVersions, getDocumentAudit,
  getExpiringDocuments
} from '../../services/supplierApi';
import { downloadFile } from '../../lib/utils';

// ── Constants ─────────────────────────────────────────────────────────────────
const CATEGORIES = [
  'GENERAL','CERTIFICATE','COMPLIANCE','INSURANCE','INVOICE',
  'SHIPPING','INSPECTION','FACTORY_IMAGE','WAREHOUSE_IMAGE','LOGO',
];
const STATUSES = ['ACTIVE','ARCHIVED','EXPIRED','PENDING_REVIEW'];
const CAT_ICONS = {
  CERTIFICATE: '🏅', COMPLIANCE: '⚖️', INSURANCE: '🛡️',
  INVOICE: '🧾', SHIPPING: '🚢', INSPECTION: '🔍',
  FACTORY_IMAGE: '🏭', WAREHOUSE_IMAGE: '🏪', LOGO: '✨', GENERAL: '📄',
};
const SIZE_LIMIT_MB = 50;
const PREVIEW_TYPES = ['image/jpeg','image/png','image/webp','application/pdf'];

function fmtSize(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes/1024).toFixed(1)} KB`;
  return `${(bytes/1048576).toFixed(1)} MB`;
}
function fmtDate(d) { return d ? new Date(d).toLocaleDateString() : '—'; }

// ── KPI Card ─────────────────────────────────────────────────────────────────
function KpiCard({ label, value, icon: Icon, color }) {
  return (
    <div style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 14, padding: '16px 18px', display: 'flex', alignItems: 'center', gap: 14, flex: 1, minWidth: 140 }}>
      <div style={{ width: 40, height: 40, borderRadius: 11, background: color + '18', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={19} color={color} />
      </div>
      <div>
        <div style={{ fontSize: 22, fontWeight: 800, color: '#111827' }}>{value}</div>
        <div style={{ fontSize: 12, color: '#6B7280' }}>{label}</div>
      </div>
    </div>
  );
}

// ── Category pill ─────────────────────────────────────────────────────────────
function CatPill({ cat }) {
  return (
    <span style={{ background: '#F3F4F6', color: '#374151', borderRadius: 99, padding: '2px 10px', fontSize: 11, fontWeight: 600 }}>
      {CAT_ICONS[cat] || '📄'} {cat}
    </span>
  );
}

// ── Slide-over ────────────────────────────────────────────────────────────────
function SlideOver({ open, onClose, title, width = 600, children }) {
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

// ── Upload Form ───────────────────────────────────────────────────────────────
function UploadForm({ onUploaded, onClose }) {
  const [file, setFile]       = useState(null);
  const [category, setCategory] = useState('GENERAL');
  const [displayName, setDisplayName] = useState('');
  const [description, setDescription] = useState('');
  const [documentDate, setDocumentDate] = useState('');
  const [expiryDate, setExpiryDate]   = useState('');
  const [issuingBody, setIssuingBody] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress]   = useState(0);
  const [err, setErr]             = useState('');
  const dropRef = useRef(null);

  const inp = { width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '9px 12px', fontSize: 13, boxSizing: 'border-box', outline: 'none' };
  const lbl = { fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 5 };

  function onDrop(e) {
    e.preventDefault();
    const f = e.dataTransfer?.files?.[0];
    if (f) pickFile(f);
  }
  function pickFile(f) {
    if (f.size > SIZE_LIMIT_MB * 1024 * 1024) { setErr(`File exceeds ${SIZE_LIMIT_MB} MB limit`); return; }
    setFile(f);
    if (!displayName) setDisplayName(f.name.replace(/\.[^.]+$/, ''));
    setErr('');
  }

  async function submit(e) {
    e.preventDefault();
    if (!file) { setErr('Please select a file'); return; }
    setUploading(true); setProgress(10); setErr('');
    try {
      const meta = { category, display_name: displayName, description, document_date: documentDate || undefined, expiry_date: expiryDate || undefined, issuing_body: issuingBody || undefined };
      setProgress(40);
      const doc = await uploadDocument(file, meta);
      setProgress(100);
      onUploaded(doc);
    } catch (e) { setErr(e.message || 'Upload failed'); setUploading(false); setProgress(0); }
  }

  return (
    <form onSubmit={submit} style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'grid', gap: 14, gridTemplateColumns: '1fr 1fr', alignContent: 'start' }}>
        {/* Drop zone */}
        <div style={{ gridColumn: 'span 2' }}
          ref={dropRef}
          onDragOver={e=>e.preventDefault()} onDrop={onDrop}>
          <div style={{ border: `2px dashed ${file ? '#10B981' : '#D1D5DB'}`, borderRadius: 12, padding: 28, textAlign: 'center', background: file ? '#ECFDF5' : '#F9FAFB', cursor: 'pointer', transition: 'all 0.2s' }}
            onClick={() => document.getElementById('doc-file-input').click()}>
            <input id="doc-file-input" type="file" style={{ display: 'none' }} onChange={e => e.target.files[0] && pickFile(e.target.files[0])} />
            {file ? (
              <>
                <FileCheck size={32} color="#10B981" style={{ marginBottom: 8 }} />
                <div style={{ fontSize: 14, fontWeight: 700, color: '#065F46' }}>{file.name}</div>
                <div style={{ fontSize: 12, color: '#6B7280' }}>{fmtSize(file.size)}</div>
              </>
            ) : (
              <>
                <Upload size={28} color="#9CA3AF" style={{ marginBottom: 8 }} />
                <div style={{ fontSize: 14, fontWeight: 600, color: '#374151', marginBottom: 4 }}>Drop file here or click to browse</div>
                <div style={{ fontSize: 12, color: '#9CA3AF' }}>PDF, JPEG, PNG, DOCX, XLSX, CSV — max {SIZE_LIMIT_MB} MB</div>
              </>
            )}
          </div>
        </div>
        <div style={{ gridColumn: 'span 2' }}>
          <label style={lbl}>Display Name</label>
          <input style={inp} value={displayName} onChange={e => setDisplayName(e.target.value)} placeholder="Friendly document name" />
        </div>
        <div>
          <label style={lbl}>Category</label>
          <select style={inp} value={category} onChange={e => setCategory(e.target.value)}>
            {CATEGORIES.map(c => <option key={c} value={c}>{CAT_ICONS[c]} {c}</option>)}
          </select>
        </div>
        <div>
          <label style={lbl}>Issuing Body</label>
          <input style={inp} value={issuingBody} onChange={e => setIssuingBody(e.target.value)} placeholder="Bureau Veritas, KPMG…" />
        </div>
        <div>
          <label style={lbl}>Document Date</label>
          <input type="date" style={inp} value={documentDate} onChange={e => setDocumentDate(e.target.value)} />
        </div>
        <div>
          <label style={lbl}>Expiry Date</label>
          <input type="date" style={inp} value={expiryDate} onChange={e => setExpiryDate(e.target.value)} />
        </div>
        <div style={{ gridColumn: 'span 2' }}>
          <label style={lbl}>Description</label>
          <textarea style={{ ...inp, resize: 'vertical', minHeight: 60 }} value={description} onChange={e => setDescription(e.target.value)} placeholder="Brief description of this document…" />
        </div>
        {uploading && (
          <div style={{ gridColumn: 'span 2' }}>
            <div style={{ background: '#E5E7EB', borderRadius: 99, height: 6, overflow: 'hidden' }}>
              <motion.div animate={{ width: `${progress}%` }} transition={{ duration: 0.5 }}
                style={{ height: '100%', background: 'linear-gradient(90deg, #10B981, #059669)', borderRadius: 99 }} />
            </div>
            <div style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>Uploading to Supabase Storage…</div>
          </div>
        )}
      </div>
      {err && <div style={{ padding: '0 24px 10px', fontSize: 13, color: '#EF4444', fontWeight: 600 }}>{err}</div>}
      <div style={{ padding: '16px 24px', borderTop: '1px solid #F3F4F6', display: 'flex', gap: 10, justifyContent: 'flex-end', background: '#FAFAFA' }}>
        <button type="button" onClick={onClose} style={{ padding: '9px 18px', border: '1.5px solid #E5E7EB', borderRadius: 8, background: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Cancel</button>
        <button type="submit" disabled={uploading || !file} style={{ padding: '9px 22px', border: 'none', borderRadius: 8, background: uploading||!file ? '#D1FAE5' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', fontSize: 13, fontWeight: 700, cursor: uploading||!file ? 'default' : 'pointer' }}>
          {uploading ? 'Uploading…' : 'Upload Document'}
        </button>
      </div>
    </form>
  );
}

// ── Edit Metadata Form ────────────────────────────────────────────────────────
function EditDocForm({ doc, onSave, onClose }) {
  const [form, setForm] = useState({
    display_name: doc.display_name || '',
    description: doc.description || '',
    category: doc.category || 'GENERAL',
    issuing_body: doc.issuing_body || '',
    document_date: doc.document_date || '',
    expiry_date: doc.expiry_date || '',
    status: doc.status || 'ACTIVE',
  });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const inp = { width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '9px 12px', fontSize: 13, boxSizing: 'border-box', outline: 'none' };
  const lbl = { fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 5 };
  async function submit(e) {
    e.preventDefault(); setSaving(true);
    try { await onSave(form); } catch {} finally { setSaving(false); }
  }
  return (
    <form onSubmit={submit} style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'grid', gap: 14, gridTemplateColumns: '1fr 1fr', alignContent: 'start' }}>
        <div style={{ gridColumn: 'span 2' }}>
          <label style={lbl}>Display Name</label>
          <input style={inp} value={form.display_name} onChange={e => set('display_name', e.target.value)} />
        </div>
        <div>
          <label style={lbl}>Category</label>
          <select style={inp} value={form.category} onChange={e => set('category', e.target.value)}>
            {CATEGORIES.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label style={lbl}>Status</label>
          <select style={inp} value={form.status} onChange={e => set('status', e.target.value)}>
            {STATUSES.map(s => <option key={s}>{s.replace('_', ' ')}</option>)}
          </select>
        </div>
        <div>
          <label style={lbl}>Issuing Body</label>
          <input style={inp} value={form.issuing_body} onChange={e => set('issuing_body', e.target.value)} />
        </div>
        <div>
          <label style={lbl}>Document Date</label>
          <input type="date" style={inp} value={form.document_date || ''} onChange={e => set('document_date', e.target.value)} />
        </div>
        <div style={{ gridColumn: 'span 2' }}>
          <label style={lbl}>Expiry Date</label>
          <input type="date" style={inp} value={form.expiry_date || ''} onChange={e => set('expiry_date', e.target.value)} />
        </div>
        <div style={{ gridColumn: 'span 2' }}>
          <label style={lbl}>Description</label>
          <textarea style={{ ...inp, resize: 'vertical', minHeight: 72 }} value={form.description} onChange={e => set('description', e.target.value)} />
        </div>
      </div>
      <div style={{ padding: '16px 24px', borderTop: '1px solid #F3F4F6', display: 'flex', gap: 10, justifyContent: 'flex-end', background: '#FAFAFA' }}>
        <button type="button" onClick={onClose} style={{ padding: '9px 18px', border: '1.5px solid #E5E7EB', borderRadius: 8, background: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Cancel</button>
        <button type="submit" disabled={saving} style={{ padding: '9px 22px', border: 'none', borderRadius: 8, background: saving ? '#D1FAE5' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', fontSize: 13, fontWeight: 700, cursor: saving ? 'default' : 'pointer' }}>
          {saving ? 'Saving…' : 'Update'}
        </button>
      </div>
    </form>
  );
}

// ── Audit Log Panel ───────────────────────────────────────────────────────────
function AuditLogPanel({ docId }) {
  const [log, setLog]       = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    getDocumentAudit(docId).then(res => {
      setLog(Array.isArray(res) ? res : (res?.data ?? []));
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [docId]);
  const ACT_COLOR = { UPLOAD:'#10B981', VIEW:'#2563EB', DOWNLOAD:'#7C3AED', UPDATE:'#D97706', DELETE:'#EF4444', VERSION_CREATED:'#0891B2' };
  return (
    <div style={{ padding: 20, overflowY: 'auto', height: '100%' }}>
      {loading ? <div style={{ textAlign: 'center', color: '#9CA3AF', marginTop: 40 }}>Loading audit log…</div>
        : log.length === 0 ? <div style={{ textAlign: 'center', color: '#9CA3AF', marginTop: 40 }}>No activity yet</div>
        : log.map((e, i) => (
          <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'flex-start' }}>
            <div style={{ width: 28, height: 28, borderRadius: '50%', background: (ACT_COLOR[e.action] || '#6B7280') + '18', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <span style={{ fontSize: 10, fontWeight: 800, color: ACT_COLOR[e.action] || '#6B7280' }}>{e.action?.[0] || '?'}</span>
            </div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#374151' }}>{e.action?.replace(/_/g,' ')}</div>
              <div style={{ fontSize: 11, color: '#9CA3AF' }}>{e.created_at ? new Date(e.created_at).toLocaleString() : ''}{e.ip_address ? ` · ${e.ip_address}` : ''}</div>
            </div>
          </div>
        ))
      }
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function DocumentCenter() {
  const [docs, setDocs]           = useState([]);
  const [expiring, setExpiring]   = useState([]);
  const [loading, setLoading]     = useState(true);
  const [total, setTotal]         = useState(0);
  const [page, setPage]           = useState(1);

  const [search, setSearch]           = useState('');
  const [filterCat, setFilterCat]     = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const [uploadOpen, setUploadOpen]   = useState(false);
  const [editDoc, setEditDoc]         = useState(null);
  const [auditDocId, setAuditDocId]   = useState(null);
  const [previewDoc, setPreviewDoc]   = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting]       = useState(false);

  const PAGE_SIZE = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: PAGE_SIZE };
      if (search)       params.search   = search;
      if (filterCat)    params.category = filterCat;
      if (filterStatus) params.status   = filterStatus;
      const [docsRes, expiryRes] = await Promise.allSettled([
        getDocuments(params), getExpiringDocuments(30)
      ]);
      if (docsRes.status === 'fulfilled') {
        const d = docsRes.value;
        const rows = Array.isArray(d) ? d : (d?.items ?? d?.data ?? []);
        setDocs(rows);
        setTotal(d?.total ?? rows.length);
      }
      if (expiryRes.status === 'fulfilled') {
        const e = expiryRes.value;
        setExpiring(Array.isArray(e) ? e : (e?.data ?? []));
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [page, search, filterCat, filterStatus]);

  useEffect(() => { load(); }, [load]);

  async function handleUpdate(data) {
    await updateDocument(editDoc.id, data);
    setEditDoc(null);
    load();
  }
  async function handleDelete() {
    setDeleting(true);
    await deleteDocument(deleteTarget.id);
    setDeleting(false);
    setDeleteTarget(null);
    load();
  }

  // Derive KPIs
  const kpiTotal    = total;
  const kpiActive   = docs.filter(d => d.status === 'ACTIVE').length;
  const kpiExpiring = expiring.length;
  const kpiCerts    = docs.filter(d => d.category === 'CERTIFICATE').length;

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileText size={20} color="#2563EB" />
          </div>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', margin: 0 }}>Document Center</h1>
            <p style={{ fontSize: 13, color: '#6B7280', margin: 0 }}>Certificates, compliance files, contracts &amp; more — stored in Supabase</p>
          </div>
        </div>
        <button onClick={() => setUploadOpen(true)}
          style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', border: 'none', borderRadius: 10, background: 'linear-gradient(135deg, #2563EB, #1D4ED8)', color: 'white', fontSize: 14, fontWeight: 700, cursor: 'pointer', boxShadow: '0 2px 8px rgba(37,99,235,0.3)' }}>
          <Upload size={16} /> Upload Document
        </button>
      </div>

      {/* KPIs */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 24, flexWrap: 'wrap' }}>
        <KpiCard label="Total Documents" value={kpiTotal} icon={FileText} color="#2563EB" />
        <KpiCard label="Active" value={kpiActive} icon={CheckCircle} color="#10B981" />
        <KpiCard label="Expiring Soon (30d)" value={kpiExpiring} icon={AlertTriangle} color="#F59E0B" />
        <KpiCard label="Certificates" value={kpiCerts} icon={Shield} color="#7C3AED" />
      </div>

      {/* Expiring warning */}
      {expiring.length > 0 && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          style={{ background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 12, padding: '12px 18px', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
          <AlertTriangle size={16} color="#D97706" />
          <span style={{ fontSize: 13, fontWeight: 600, color: '#92400E' }}>
            {expiring.length} document{expiring.length > 1 ? 's' : ''} expiring within 30 days —&nbsp;
            {expiring.map(d => d.display_name || d.file_name).join(', ')}
          </span>
        </motion.div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 18, background: 'white', borderRadius: 12, padding: '14px 18px', border: '1px solid #E5E7EB', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
          <Search size={14} color="#9CA3AF" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
          <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Search documents…"
            style={{ width: '100%', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '8px 12px 8px 34px', fontSize: 13, outline: 'none', boxSizing: 'border-box' }} />
        </div>
        <select value={filterCat} onChange={e => { setFilterCat(e.target.value); setPage(1); }}
          style={{ border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '8px 12px', fontSize: 13, outline: 'none', background: 'white', minWidth: 140 }}>
          <option value="">All Categories</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{CAT_ICONS[c]} {c}</option>)}
        </select>
        <select value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setPage(1); }}
          style={{ border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '8px 12px', fontSize: 13, outline: 'none', background: 'white', minWidth: 140 }}>
          <option value="">All Statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
        </select>
        <button onClick={load} style={{ padding: '8px 14px', border: '1.5px solid #E5E7EB', borderRadius: 8, background: 'white', cursor: 'pointer', color: '#6B7280', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {/* Table */}
      <div style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 14, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 60, textAlign: 'center', color: '#9CA3AF' }}>
            <div style={{ width: 36, height: 36, border: '3px solid #E5E7EB', borderTopColor: '#2563EB', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px' }} />
            <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
            Loading documents…
          </div>
        ) : docs.length === 0 ? (
          <div style={{ padding: 60, textAlign: 'center' }}>
            <FolderOpen size={44} color="#E5E7EB" style={{ marginBottom: 12 }} />
            <div style={{ fontSize: 16, fontWeight: 700, color: '#374151', marginBottom: 6 }}>No documents yet</div>
            <div style={{ fontSize: 13, color: '#9CA3AF', marginBottom: 18 }}>Upload your first document — certificates, compliance files, factory images and more</div>
            <button onClick={() => setUploadOpen(true)} style={{ padding: '9px 20px', border: 'none', borderRadius: 9, background: 'linear-gradient(135deg, #2563EB, #1D4ED8)', color: 'white', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>↑ Upload Document</button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#F9FAFB', borderBottom: '1px solid #E5E7EB' }}>
                  {['Document','Category','Type','Size','Status','Doc Date','Expiry','Version','Actions'].map(h => (
                    <th key={h} style={{ padding: '11px 14px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {docs.map((d, i) => {
                  const isExpired   = d.expiry_date && new Date(d.expiry_date) < new Date();
                  const isExpiring  = !isExpired && d.expiry_date && new Date(d.expiry_date) < new Date(Date.now() + 30*86400000);
                  return (
                    <tr key={d.id} style={{ borderBottom: '1px solid #F3F4F6', background: i%2===0?'white':'#FAFAFA' }}
                      onMouseEnter={e => e.currentTarget.style.background='#EFF6FF'}
                      onMouseLeave={e => e.currentTarget.style.background=i%2===0?'white':'#FAFAFA'}>
                      <td style={{ padding: '11px 14px' }}>
                        <div style={{ fontWeight: 700, color: '#111827', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={d.display_name || d.file_name}>
                          {d.display_name || d.file_name}
                        </div>
                        <div style={{ fontSize: 11, color: '#9CA3AF', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }}>{d.file_name}</div>
                      </td>
                      <td style={{ padding: '11px 14px' }}><CatPill cat={d.category} /></td>
                      <td style={{ padding: '11px 14px', color: '#6B7280' }}>{d.content_type?.split('/')[1]?.toUpperCase() || '—'}</td>
                      <td style={{ padding: '11px 14px', color: '#6B7280', whiteSpace: 'nowrap' }}>{fmtSize(d.size_bytes)}</td>
                      <td style={{ padding: '11px 14px' }}>
                        <span style={{ background: d.status==='ACTIVE'?'#ECFDF5':d.status==='EXPIRED'?'#FEF2F2':'#F3F4F6', color: d.status==='ACTIVE'?'#059669':d.status==='EXPIRED'?'#DC2626':'#374151', borderRadius: 99, padding: '2px 10px', fontSize: 11, fontWeight: 700 }}>
                          {d.status}
                        </span>
                      </td>
                      <td style={{ padding: '11px 14px', color: '#6B7280', whiteSpace: 'nowrap' }}>{fmtDate(d.document_date)}</td>
                      <td style={{ padding: '11px 14px', whiteSpace: 'nowrap' }}>
                        <span style={{ color: isExpired?'#EF4444':isExpiring?'#D97706':'#6B7280', fontWeight: isExpired||isExpiring?700:400 }}>
                          {d.expiry_date ? fmtDate(d.expiry_date) : '—'}
                          {isExpired && ' ⚠️'}
                          {isExpiring && !isExpired && ' ⏰'}
                        </span>
                      </td>
                      <td style={{ padding: '11px 14px', color: '#6B7280', textAlign: 'center' }}>v{d.version}</td>
                      <td style={{ padding: '11px 14px' }}>
                        <div style={{ display: 'flex', gap: 5 }}>
                          {PREVIEW_TYPES.includes(d.content_type) && (
                            <button onClick={() => setPreviewDoc(d)} title="Preview Document"
                              style={{ background: '#EFF6FF', border: 'none', borderRadius: 6, padding: '5px 7px', cursor: 'pointer', color: '#2563EB', display: 'inline-flex', alignItems: 'center' }}>
                              <Eye size={13} />
                            </button>
                          )}
                          <button onClick={() => downloadFile(d.public_url, d.display_name || d.file_name)} title="Download"
                            style={{ background: '#F0FDF4', border: 'none', borderRadius: 6, padding: '5px 7px', cursor: 'pointer', color: '#059669', display: 'inline-flex', alignItems: 'center' }}>
                            <Download size={13} />
                          </button>
                          <button onClick={() => setAuditDocId(d.id)} title="Audit Log"
                            style={{ background: '#F5F3FF', border: 'none', borderRadius: 6, padding: '5px 7px', cursor: 'pointer', color: '#7C3AED' }}><History size={13} /></button>
                          <button onClick={() => setEditDoc(d)} title="Edit"
                            style={{ background: '#FEF9C3', border: 'none', borderRadius: 6, padding: '5px 7px', cursor: 'pointer', color: '#D97706' }}>
                            <FileText size={13} />
                          </button>
                          <button onClick={() => setDeleteTarget(d)} title="Delete"
                            style={{ background: '#FEF2F2', border: 'none', borderRadius: 6, padding: '5px 7px', cursor: 'pointer', color: '#EF4444' }}><Trash2 size={13} /></button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {total > PAGE_SIZE && (
          <div style={{ padding: '12px 18px', borderTop: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 12, color: '#9CA3AF' }}>Showing {((page-1)*PAGE_SIZE)+1}–{Math.min(page*PAGE_SIZE, total)} of {total}</span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={() => setPage(p=>Math.max(p-1,1))} disabled={page===1}
                style={{ padding: '6px 12px', border: '1px solid #E5E7EB', borderRadius: 7, background: 'white', cursor: page===1?'default':'pointer', opacity: page===1?0.4:1, fontSize: 13 }}>← Prev</button>
              <button onClick={() => setPage(p=>p+1)} disabled={page*PAGE_SIZE>=total}
                style={{ padding: '6px 12px', border: '1px solid #E5E7EB', borderRadius: 7, background: 'white', cursor: page*PAGE_SIZE>=total?'default':'pointer', opacity: page*PAGE_SIZE>=total?0.4:1, fontSize: 13 }}>Next →</button>
            </div>
          </div>
        )}
      </div>

      {/* Document Preview Lightbox Modal */}
      <AnimatePresence>
        {previewDoc && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', zIndex: 250, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
            <motion.div initial={{ scale: 0.94, y: 10 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.94, y: 10 }}
              style={{ background: 'white', borderRadius: 16, width: '100%', maxWidth: 840, maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column', boxShadow: '0 25px 60px rgba(0,0,0,0.3)' }}>
              
              {/* Header */}
              <div style={{ padding: '16px 20px', borderBottom: '1px solid #E5E7EB', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#FAFAFA' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <FileText size={18} color="#2563EB" />
                  <div>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: '#111827', margin: 0 }}>
                      {previewDoc.display_name || previewDoc.file_name}
                    </h3>
                    <div style={{ fontSize: 11, color: '#6B7280' }}>
                      {previewDoc.category} · {fmtSize(previewDoc.size_bytes)} · v{previewDoc.version}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <a href={previewDoc.public_url} target="_blank" rel="noopener noreferrer"
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 12px', borderRadius: 7, border: '1px solid #E5E7EB', background: 'white', fontSize: 12, fontWeight: 600, color: '#374151', textDecoration: 'none' }}>
                    <ExternalLink size={13} /> Open in New Tab
                  </a>
                  <button onClick={() => downloadFile(previewDoc.public_url, previewDoc.display_name || previewDoc.file_name)}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 14px', borderRadius: 7, background: '#10B981', border: 'none', fontSize: 12, fontWeight: 700, color: 'white', cursor: 'pointer' }}>
                    <Download size={13} /> Download
                  </button>
                  <button onClick={() => setPreviewDoc(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF', padding: 4 }}>
                    <X size={20} />
                  </button>
                </div>
              </div>

              {/* Preview Body */}
              <div style={{ flex: 1, background: '#111827', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'auto', padding: 20, minHeight: 400 }}>
                {previewDoc.content_type?.startsWith('image/') ? (
                  <img src={previewDoc.public_url} alt={previewDoc.display_name || previewDoc.file_name}
                    style={{ maxWidth: '100%', maxHeight: '70vh', objectFit: 'contain', borderRadius: 8, boxShadow: '0 8px 30px rgba(0,0,0,0.5)' }} />
                ) : previewDoc.content_type === 'application/pdf' ? (
                  <iframe src={previewDoc.public_url} title="PDF Preview"
                    style={{ width: '100%', height: '70vh', border: 'none', borderRadius: 8 }} />
                ) : (
                  <div style={{ color: 'white', textAlign: 'center' }}>
                    <FileText size={48} style={{ opacity: 0.5, marginBottom: 12 }} />
                    <div>Preview not available for this file type.</div>
                  </div>
                )}
              </div>

            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload Panel */}
      <SlideOver open={uploadOpen} onClose={() => setUploadOpen(false)} title="Upload Document">
        <UploadForm onUploaded={() => { setUploadOpen(false); load(); }} onClose={() => setUploadOpen(false)} />
      </SlideOver>

      {/* Edit Panel */}
      <SlideOver open={!!editDoc} onClose={() => setEditDoc(null)} title="Edit Document Metadata">
        {editDoc && <EditDocForm doc={editDoc} onSave={handleUpdate} onClose={() => setEditDoc(null)} />}
      </SlideOver>

      {/* Audit Log Panel */}
      <SlideOver open={!!auditDocId} onClose={() => setAuditDocId(null)} title="Document Audit Log" width={480}>
        {auditDocId && <AuditLogPanel docId={auditDocId} />}
      </SlideOver>

      {/* Delete Confirm */}
      <AnimatePresence>
        {deleteTarget && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }}
              style={{ background: 'white', borderRadius: 16, padding: 28, maxWidth: 400, width: '90%', boxShadow: '0 8px 40px rgba(0,0,0,0.15)' }}>
              <div style={{ fontSize: 16, fontWeight: 800, color: '#111827', marginBottom: 10 }}>Delete Document?</div>
              <div style={{ fontSize: 13, color: '#6B7280', marginBottom: 22 }}>
                <strong>{deleteTarget.display_name || deleteTarget.file_name}</strong> will be permanently deleted from Supabase Storage and cannot be recovered.
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button onClick={() => setDeleteTarget(null)} style={{ padding: '9px 18px', border: '1.5px solid #E5E7EB', borderRadius: 8, background: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Cancel</button>
                <button onClick={handleDelete} disabled={deleting} style={{ padding: '9px 18px', border: 'none', borderRadius: 8, background: '#EF4444', color: 'white', fontSize: 13, fontWeight: 700, cursor: deleting?'default':'pointer' }}>
                  {deleting ? 'Deleting…' : 'Delete Permanently'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
