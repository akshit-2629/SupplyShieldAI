/**
 * PendingInvitations.jsx — Manage all sent invitations.
 */

import { useState, useEffect, useCallback } from 'react';
import { Send, Clock, CheckCircle2, XCircle, RefreshCw, RotateCcw, X, AlertCircle, Mail, Copy, Check } from 'lucide-react';
import { listInvitations, resendInvitation, cancelInvitation } from '../../services/supplierManagementApi';

const STATUS_META = {
  PENDING:   { label: 'Pending',   color: '#F59E0B', bg: '#FEF3C7', icon: Clock },
  ACCEPTED:  { label: 'Accepted',  color: '#10B981', bg: '#D1FAE5', icon: CheckCircle2 },
  EXPIRED:   { label: 'Expired',   color: '#9CA3AF', bg: '#F3F4F6', icon: AlertCircle },
  CANCELLED: { label: 'Cancelled', color: '#EF4444', bg: '#FEE2E2', icon: XCircle },
};

function countdown(expiresAt) {
  const ms = new Date(expiresAt) - Date.now();
  if (ms <= 0) return 'Expired';
  const d = Math.floor(ms / 86400000);
  const h = Math.floor((ms % 86400000) / 3600000);
  return d > 0 ? `${d}d ${h}h remaining` : `${h}h remaining`;
}

export default function PendingInvitations({ onInvite }) {
  const [rows, setRows]       = useState([]);
  const [total, setTotal]     = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter]   = useState('');
  const [actionId, setActionId] = useState(null);
  const [actionType, setActionType] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [copiedToken, setCopiedToken] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listInvitations({ status: filter || undefined, pageSize: 100 });
      setRows(res.data || []);
      setTotal(res.total || 0);
    } catch (_) {}
    setLoading(false);
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  async function doAction(id, type) {
    setActionLoading(true);
    try {
      if (type === 'resend') await resendInvitation(id);
      if (type === 'cancel') await cancelInvitation(id);
      await load();
    } catch (_) {}
    setActionId(null);
    setActionType(null);
    setActionLoading(false);
  }

  function handleCopyLink(token) {
    const url = `${window.location.origin}/supplier/register?token=${token}`;
    navigator.clipboard.writeText(url);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2500);
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 24px', borderBottom: '1px solid #F3F4F6', flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', gap: 6 }}>
          {[['', 'All'], ['PENDING', 'Pending'], ['ACCEPTED', 'Accepted'], ['EXPIRED', 'Expired'], ['CANCELLED', 'Cancelled']].map(([v, l]) => (
            <button key={v} onClick={() => setFilter(v)} style={{
              padding: '5px 12px', borderRadius: 999, fontSize: 12, fontWeight: 600, cursor: 'pointer',
              border: `1.5px solid ${filter === v ? '#2563EB' : '#E5E7EB'}`,
              background: filter === v ? '#EFF6FF' : 'white',
              color: filter === v ? '#2563EB' : '#6B7280',
            }}>{l}</button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={load} style={iconBtn}><RefreshCw size={13} color="#6B7280" /></button>
          <button onClick={onInvite} style={primaryBtn}><Send size={13} /> New Invitation</button>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, gap: 10 }}>
          <RefreshCw size={18} color="#2563EB" style={{ animation: 'spin 1s linear infinite' }} />
          <span style={{ fontSize: 14, color: '#6B7280' }}>Loading…</span>
        </div>
      ) : rows.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 24px' }}>
          <Send size={32} color="#E5E7EB" style={{ marginBottom: 12 }} />
          <p style={{ fontSize: 14, color: '#9CA3AF', fontWeight: 600 }}>No invitations yet</p>
          <button onClick={onInvite} style={{ ...primaryBtn, marginTop: 12 }}><Send size={13} /> Invite Supplier</button>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#F9FAFB' }}>
                {['Company', 'Email', 'Contact', 'Category', 'Relationship', 'Expiry', 'Status', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(r => {
                const sm = STATUS_META[r.status] || STATUS_META.PENDING;
                const StatusIcon = sm.icon;
                return (
                  <tr key={r.id} style={{ borderBottom: '1px solid #F3F4F6' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#F9FAFB'}
                    onMouseLeave={e => e.currentTarget.style.background = 'white'}
                  >
                    <td style={{ padding: '12px 16px', fontWeight: 700, color: '#111827' }}>
                      {r.supplier_company_name}
                      {r.is_critical && <span style={{ marginLeft: 6, fontSize: 9, fontWeight: 800, color: '#EF4444', background: '#FEE2E2', padding: '1px 5px', borderRadius: 999 }}>CRIT</span>}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#374151' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                        <Mail size={12} color="#9CA3AF" />{r.supplier_email}
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#374151' }}>{r.contact_name}</td>
                    <td style={{ padding: '12px 16px', color: '#6B7280', whiteSpace: 'nowrap' }}>{r.business_category || '—'}</td>
                    <td style={{ padding: '12px 16px', color: '#6B7280', whiteSpace: 'nowrap' }}>{r.relationship_type || '—'}</td>
                    <td style={{ padding: '12px 16px', fontSize: 11, color: r.status === 'PENDING' ? '#F59E0B' : '#9CA3AF', whiteSpace: 'nowrap' }}>
                      {r.status === 'PENDING' ? countdown(r.expires_at) : (r.accepted_at ? new Date(r.accepted_at).toLocaleDateString('en-GB') : new Date(r.expires_at).toLocaleDateString('en-GB'))}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, fontWeight: 700, color: sm.color, background: sm.bg, padding: '3px 10px', borderRadius: 999 }}>
                        <StatusIcon size={10} />{sm.label}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', gap: 6 }}>
                        {r.token && (r.status === 'PENDING' || r.status === 'EXPIRED') && (
                          <button onClick={() => handleCopyLink(r.token)} style={actionBtnStyle('#10B981')}>
                            {copiedToken === r.token ? <Check size={11} /> : <Copy size={11} />}
                            {copiedToken === r.token ? 'Copied' : 'Copy Link'}
                          </button>
                        )}
                        {(r.status === 'PENDING' || r.status === 'EXPIRED') && (
                          <button onClick={() => doAction(r.id, 'resend')} disabled={actionLoading} style={actionBtnStyle('#2563EB')}>
                            <RotateCcw size={11} /> Resend
                          </button>
                        )}
                        {r.status === 'PENDING' && (
                          <button onClick={() => doAction(r.id, 'cancel')} disabled={actionLoading} style={actionBtnStyle('#EF4444')}>
                            <X size={11} /> Cancel
                          </button>
                        )}
                      </div>

                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function actionBtnStyle(color) {
  return {
    display: 'inline-flex', alignItems: 'center', gap: 4,
    padding: '4px 10px', borderRadius: 6, border: `1px solid ${color}`,
    background: 'white', color, fontSize: 11, fontWeight: 700, cursor: 'pointer',
  };
}
const iconBtn = { display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 10px', borderRadius: 7, border: '1px solid #E5E7EB', background: 'white', cursor: 'pointer' };
const primaryBtn = { display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 8, border: 'none', background: 'linear-gradient(135deg, #2563EB, #1D4ED8)', color: 'white', fontSize: 12, fontWeight: 700, cursor: 'pointer' };
