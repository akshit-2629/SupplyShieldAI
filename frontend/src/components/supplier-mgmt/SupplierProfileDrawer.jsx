/**
 * SupplierProfileDrawer.jsx — Right-side slide-in panel with full supplier profile.
 * Used from SupplierDirectory and PendingApprovals.
 */

import { useState, useEffect } from 'react';
import {
  X, Building2, MapPin, Phone, Mail, Globe, Package, Shield, Star,
  FileText, Clock, AlertCircle, CheckCircle2, XCircle, Pause, RotateCcw,
  ChevronDown, ChevronUp, Loader, PenLine, StickyNote,
} from 'lucide-react';
import {
  getSupplier, listNotes, getAuditLog, addNote,
  approveSupplier, rejectSupplier, suspendSupplier, reactivateSupplier,
} from '../../services/supplierManagementApi';

const STATUS_META = {
  APPROVED:  { label: 'Active',           color: '#10B981', bg: '#D1FAE5', icon: CheckCircle2 },
  PENDING:   { label: 'Pending Approval', color: '#F59E0B', bg: '#FEF3C7', icon: Clock },
  REJECTED:  { label: 'Rejected',         color: '#EF4444', bg: '#FEE2E2', icon: XCircle },
  SUSPENDED: { label: 'Suspended',        color: '#6B7280', bg: '#F3F4F6', icon: Pause },
};

const RISK_COLOR = { LOW: '#10B981', MEDIUM: '#F59E0B', HIGH: '#F97316', CRITICAL: '#EF4444', UNKNOWN: '#9CA3AF' };

export default function SupplierProfileDrawer({ supplierUid, onClose, onActionComplete }) {
  const [supplier, setSupplier] = useState(null);
  const [notes, setNotes]       = useState([]);
  const [audit, setAudit]       = useState([]);
  const [tab, setTab]           = useState('profile'); // profile | notes | audit
  const [loading, setLoading]   = useState(true);
  const [actionModal, setActionModal] = useState(null); // null | 'reject' | 'suspend'
  const [actionNote, setActionNote]   = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError]     = useState('');
  const [newNote, setNewNote]   = useState('');
  const [noteLoading, setNoteLoading] = useState(false);

  useEffect(() => {
    if (!supplierUid) return;
    setLoading(true);
    Promise.all([
      getSupplier(supplierUid),
      listNotes(supplierUid),
      getAuditLog(supplierUid, 30),
    ]).then(([s, n, a]) => {
      setSupplier(s);
      setNotes(n);
      setAudit(a);
    }).finally(() => setLoading(false));
  }, [supplierUid]);

  async function doAction(type) {
    setActionLoading(true);
    setActionError('');
    try {
      if (type === 'approve')    await approveSupplier(supplierUid, actionNote);
      if (type === 'reject')     await rejectSupplier(supplierUid, actionNote);
      if (type === 'suspend')    await suspendSupplier(supplierUid, actionNote);
      if (type === 'reactivate') await reactivateSupplier(supplierUid);
      setActionModal(null);
      onActionComplete?.();
      // Refresh
      const s = await getSupplier(supplierUid);
      setSupplier(s);
    } catch (e) {
      setActionError(e.message);
    } finally {
      setActionLoading(false);
    }
  }

  async function submitNote() {
    if (!newNote.trim()) return;
    setNoteLoading(true);
    try {
      const n = await addNote(supplierUid, 'INTERNAL_NOTE', newNote.trim());
      setNotes(prev => [n, ...prev]);
      setNewNote('');
    } catch (_) {}
    setNoteLoading(false);
  }

  if (loading) {
    return (
      <Drawer onClose={onClose}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 12 }}>
          <Loader size={20} color="#2563EB" style={{ animation: 'spin 1s linear infinite' }} />
          <span style={{ fontSize: 14, color: '#6B7280' }}>Loading supplier profile…</span>
        </div>
      </Drawer>
    );
  }

  if (!supplier) return null;

  const sm = STATUS_META[supplier.status] || STATUS_META.PENDING;
  const StatusIcon = sm.icon;

  return (
    <Drawer onClose={onClose}>
      {/* Header */}
      <div style={{
        padding: '20px 24px', borderBottom: '1px solid #F3F4F6',
        display: 'flex', gap: 16, alignItems: 'flex-start',
      }}>
        <div style={{
          width: 52, height: 52, borderRadius: 12, background: '#EFF6FF',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, overflow: 'hidden',
        }}>
          {supplier.logo_url
            ? <img src={supplier.logo_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            : <Building2 size={22} color="#2563EB" />}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <h2 style={{ fontSize: 16, fontWeight: 800, color: '#111827', margin: 0 }}>
              {supplier.company_name}
            </h2>
            {supplier.is_critical && (
              <span style={{ fontSize: 10, fontWeight: 700, color: '#EF4444', background: '#FEE2E2', padding: '2px 8px', borderRadius: 999 }}>
                CRITICAL
              </span>
            )}
          </div>
          <div style={{ fontSize: 12, color: '#6B7280', marginTop: 3 }}>
            {supplier.supplier_code} · {supplier.email}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              fontSize: 11, fontWeight: 700, color: sm.color, background: sm.bg,
              padding: '3px 10px', borderRadius: 999,
            }}>
              <StatusIcon size={11} />{sm.label}
            </span>
            <span style={{
              fontSize: 11, fontWeight: 700, color: RISK_COLOR[supplier.risk_rating] || '#9CA3AF',
              background: '#F9FAFB', border: '1px solid #E5E7EB', padding: '3px 10px', borderRadius: 999,
            }}>
              Risk: {supplier.risk_rating || 'UNKNOWN'}
            </span>
          </div>
        </div>
        <button onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 4, flexShrink: 0 }}>
          <X size={18} color="#6B7280" />
        </button>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: 8, padding: '12px 24px', borderBottom: '1px solid #F3F4F6', flexWrap: 'wrap' }}>
        {supplier.status === 'PENDING' && <>
          <ActionBtn color="#10B981" onClick={() => { setActionNote(''); setActionModal('approve'); }}>
            <CheckCircle2 size={12} /> Approve
          </ActionBtn>
          <ActionBtn color="#EF4444" onClick={() => { setActionNote(''); setActionModal('reject'); }}>
            <XCircle size={12} /> Reject
          </ActionBtn>
        </>}
        {supplier.status === 'APPROVED' && (
          <ActionBtn color="#F59E0B" onClick={() => { setActionNote(''); setActionModal('suspend'); }}>
            <Pause size={12} /> Suspend
          </ActionBtn>
        )}
        {supplier.status === 'SUSPENDED' && (
          <ActionBtn color="#10B981" onClick={() => doAction('reactivate')}>
            <RotateCcw size={12} /> Reactivate
          </ActionBtn>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #F3F4F6', padding: '0 24px' }}>
        {[['profile', 'Profile'], ['notes', `Notes (${notes.length})`], ['audit', 'Audit Log']].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)} style={{
            padding: '10px 14px', fontSize: 13, fontWeight: tab === key ? 700 : 500,
            color: tab === key ? '#2563EB' : '#6B7280',
            borderBottom: tab === key ? '2px solid #2563EB' : '2px solid transparent',
            background: 'none', border: 'none', borderRadius: 0, cursor: 'pointer',
          }}>{label}</button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1 }}>

        {/* ── Profile ── */}
        {tab === 'profile' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Section title="Company Information" icon={Building2}>
              <InfoRow label="Company"     value={supplier.company_name} />
              <InfoRow label="Code"        value={supplier.supplier_code} />
              <InfoRow label="Contact"     value={supplier.contact_name} />
              <InfoRow label="Email"       value={supplier.email} />
              <InfoRow label="Phone"       value={supplier.phone} />
              <InfoRow label="Website"     value={supplier.website} />
              <InfoRow label="Country"     value={[supplier.headquarters_city, supplier.headquarters_country].filter(Boolean).join(', ')} />
              <InfoRow label="Description" value={supplier.description} />
            </Section>

            <Section title="Business" icon={Package}>
              <InfoRow label="Categories"
                value={(supplier.manufacturing_categories || []).join(', ')} />
              <InfoRow label="Relationship" value={supplier.relationship_type} />
            </Section>

            {(supplier.certifications || []).length > 0 && (
              <Section title="Certifications" icon={Shield}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {supplier.certifications.map((c, i) => (
                    <span key={i} style={{ fontSize: 11, fontWeight: 600, color: '#2563EB', background: '#EFF6FF', padding: '3px 10px', borderRadius: 999 }}>
                      {typeof c === 'string' ? c : c.name}
                    </span>
                  ))}
                </div>
              </Section>
            )}

            {(supplier.documents || []).length > 0 && (
              <Section title="Documents" icon={FileText}>
                {supplier.documents.map((d, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0' }}>
                    <FileText size={14} color="#6B7280" />
                    <a href={d.url || '#'} target="_blank" rel="noreferrer"
                      style={{ fontSize: 13, color: '#2563EB', fontWeight: 600 }}>
                      {d.name || `Document ${i + 1}`}
                    </a>
                    {d.type && <span style={{ fontSize: 11, color: '#9CA3AF' }}>{d.type}</span>}
                  </div>
                ))}
              </Section>
            )}

            {supplier.rejection_reason && (
              <div style={{
                background: '#FEF2F2', border: '1px solid #FECACA',
                borderRadius: 8, padding: '12px 16px',
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#DC2626', marginBottom: 4 }}>Rejection Reason</div>
                <p style={{ fontSize: 13, color: '#7F1D1D', margin: 0 }}>{supplier.rejection_reason}</p>
              </div>
            )}
          </div>
        )}

        {/* ── Notes ── */}
        {tab === 'notes' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <textarea
                value={newNote} onChange={e => setNewNote(e.target.value)}
                placeholder="Add internal note…"
                rows={2}
                style={{
                  flex: 1, border: '1px solid #E5E7EB', borderRadius: 8,
                  padding: '8px 12px', fontSize: 13, resize: 'vertical',
                  outline: 'none', boxSizing: 'border-box',
                }}
              />
              <button onClick={submitNote} disabled={noteLoading || !newNote.trim()} style={{
                padding: '8px 14px', borderRadius: 8, border: 'none',
                background: '#2563EB', color: 'white', fontSize: 12,
                fontWeight: 700, cursor: 'pointer', flexShrink: 0, alignSelf: 'flex-start',
              }}>
                {noteLoading ? <Loader size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <PenLine size={12} />}
              </button>
            </div>
            {notes.length === 0 && (
              <div style={{ textAlign: 'center', padding: '32px', color: '#9CA3AF', fontSize: 13 }}>
                No notes yet
              </div>
            )}
            {notes.map(n => (
              <div key={n.id} style={{ background: '#FAFAFA', border: '1px solid #F3F4F6', borderRadius: 8, padding: '12px 14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: noteTypeColor(n.note_type), background: noteTypeBg(n.note_type), padding: '2px 8px', borderRadius: 999 }}>
                    {n.note_type.replace(/_/g, ' ')}
                  </span>
                  <span style={{ fontSize: 11, color: '#9CA3AF' }}>{fmtDate(n.created_at)}</span>
                </div>
                <p style={{ fontSize: 13, color: '#374151', margin: 0, lineHeight: 1.6 }}>{n.content}</p>
              </div>
            ))}
          </div>
        )}

        {/* ── Audit Log ── */}
        {tab === 'audit' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {audit.length === 0 && (
              <div style={{ textAlign: 'center', padding: '32px', color: '#9CA3AF', fontSize: 13 }}>No audit events</div>
            )}
            {audit.map((e, i) => (
              <div key={e.id} style={{
                display: 'flex', gap: 12, paddingBottom: 16,
                borderLeft: i < audit.length - 1 ? '2px solid #E5E7EB' : 'none',
                marginLeft: 6, paddingLeft: 16, paddingTop: i === 0 ? 0 : 0,
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', background: '#EFF6FF',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, marginLeft: -22, border: '2px solid #DBEAFE',
                }}>
                  <Clock size={12} color="#2563EB" />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>
                    {e.action.replace(/_/g, ' ')}
                  </div>
                  <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2 }}>
                    {fmtDate(e.created_at)} · {e.actor_role}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Modal */}
      {actionModal && (
        <div style={overlayStyle}>
          <div style={{ background: 'white', borderRadius: 12, padding: 24, width: 380, boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }}>
            <h3 style={{ fontSize: 15, fontWeight: 800, color: '#111827', marginBottom: 8 }}>
              {actionModal === 'approve' ? 'Approve Supplier' : actionModal === 'reject' ? 'Reject Supplier' : 'Suspend Supplier'}
            </h3>
            <p style={{ fontSize: 13, color: '#6B7280', marginBottom: 12 }}>
              {actionModal === 'approve'
                ? 'This will grant the supplier full portal access.'
                : actionModal === 'reject'
                ? 'Please provide a reason for rejection.'
                : 'Provide a reason for suspension.'}
            </p>
            <textarea
              value={actionNote} onChange={e => setActionNote(e.target.value)}
              placeholder={actionModal === 'approve' ? 'Optional note…' : 'Required reason…'}
              rows={3}
              style={{ width: '100%', boxSizing: 'border-box', border: '1px solid #E5E7EB', borderRadius: 8, padding: '8px 12px', fontSize: 13, resize: 'vertical' }}
            />
            {actionError && <p style={{ fontSize: 12, color: '#EF4444', margin: '4px 0 0' }}>{actionError}</p>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button onClick={() => setActionModal(null)} style={secondaryBtnSm}>Cancel</button>
              <button
                onClick={() => doAction(actionModal)}
                disabled={actionLoading || (actionModal !== 'approve' && !actionNote.trim())}
                style={{
                  ...primaryBtnSm,
                  background: actionModal === 'approve' ? '#10B981' : actionModal === 'reject' ? '#EF4444' : '#F59E0B',
                }}
              >
                {actionLoading ? <Loader size={12} style={{ animation: 'spin 1s linear infinite' }} /> : null}
                {actionModal === 'approve' ? 'Approve' : actionModal === 'reject' ? 'Reject' : 'Suspend'}
              </button>
            </div>
          </div>
        </div>
      )}
    </Drawer>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Drawer({ children, onClose }) {
  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.2)', zIndex: 900 }} />
      <div style={{
        position: 'fixed', top: 0, right: 0, height: '100vh', width: 480, maxWidth: '95vw',
        background: 'white', boxShadow: '-4px 0 40px rgba(0,0,0,0.12)', zIndex: 901,
        display: 'flex', flexDirection: 'column',
        animation: 'slideInRight 0.25s ease',
      }}>
        {children}
      </div>
    </>
  );
}

function Section({ title, icon: Icon, children }) {
  return (
    <div style={{ background: '#FAFAFA', border: '1px solid #F3F4F6', borderRadius: 10, padding: '14px 16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
        <Icon size={13} color="#6B7280" />
        <span style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{title}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>{children}</div>
    </div>
  );
}

function InfoRow({ label, value }) {
  if (!value) return null;
  return (
    <div style={{ display: 'flex', gap: 10, fontSize: 13, alignItems: 'flex-start' }}>
      <span style={{ minWidth: 90, flexShrink: 0, color: '#9CA3AF', fontWeight: 500 }}>{label}</span>
      <span style={{ color: '#111827', fontWeight: 500, wordBreak: 'break-word' }}>{value}</span>
    </div>
  );
}

function ActionBtn({ color, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '6px 14px', borderRadius: 7, border: `1.5px solid ${color}`,
      background: 'white', color, fontSize: 12, fontWeight: 700, cursor: 'pointer',
    }}>
      {children}
    </button>
  );
}

function noteTypeColor(t) {
  const m = { APPROVAL_NOTE: '#10B981', REJECTION_REASON: '#EF4444', REQUEST_MORE_INFO: '#F59E0B', RISK_OBSERVATION: '#F97316', INTERNAL_NOTE: '#6B7280' };
  return m[t] || '#6B7280';
}
function noteTypeBg(t) {
  const m = { APPROVAL_NOTE: '#D1FAE5', REJECTION_REASON: '#FEE2E2', REQUEST_MORE_INFO: '#FEF3C7', RISK_OBSERVATION: '#FFEDD5', INTERNAL_NOTE: '#F3F4F6' };
  return m[t] || '#F3F4F6';
}
function fmtDate(d) {
  if (!d) return '';
  return new Date(d).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

const overlayStyle = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' };
const primaryBtnSm  = { display: 'inline-flex', alignItems: 'center', gap: 5, padding: '8px 16px', borderRadius: 7, border: 'none', color: 'white', fontSize: 13, fontWeight: 700, cursor: 'pointer' };
const secondaryBtnSm = { padding: '8px 14px', borderRadius: 7, border: '1px solid #E5E7EB', background: 'white', color: '#374151', fontSize: 13, fontWeight: 600, cursor: 'pointer' };
