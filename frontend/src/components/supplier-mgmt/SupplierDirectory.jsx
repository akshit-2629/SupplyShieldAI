/**
 * SupplierDirectory.jsx — Searchable, filterable, paginated supplier table.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Search, Filter, Download, RefreshCw, Building2,
  ChevronLeft, ChevronRight, Eye, Shield, AlertCircle,
} from 'lucide-react';
import { listSuppliers, exportSuppliersCSV } from '../../services/supplierManagementApi';
import SupplierProfileDrawer from './SupplierProfileDrawer';

const STATUS_FILTERS = [
  { label: 'All',       value: '' },
  { label: 'Active',    value: 'APPROVED' },
  { label: 'Pending',   value: 'PENDING' },
  { label: 'Cancelled', value: 'CANCELLED' },
  { label: 'Suspended', value: 'SUSPENDED' },
  { label: 'Rejected',  value: 'REJECTED' },
];
const STATUS_STYLE = {
  APPROVED:  { label: 'Active',    color: '#10B981', bg: '#D1FAE5' },
  ACTIVE:    { label: 'Active',    color: '#10B981', bg: '#D1FAE5' },
  PENDING:   { label: 'Pending',   color: '#F59E0B', bg: '#FEF3C7' },
  CANCELLED: { label: 'Cancelled', color: '#6B7280', bg: '#F3F4F6' },
  EXPIRED:   { label: 'Expired',   color: '#6B7280', bg: '#F3F4F6' },
  REJECTED:  { label: 'Rejected',  color: '#EF4444', bg: '#FEE2E2' },
  SUSPENDED: { label: 'Suspended', color: '#6B7280', bg: '#F3F4F6' },
};

const RISK_COLOR = { LOW: '#10B981', MEDIUM: '#F59E0B', HIGH: '#F97316', CRITICAL: '#EF4444', UNKNOWN: '#9CA3AF' };

function useDebounce(val, delay) {
  const [d, setD] = useState(val);
  useEffect(() => { const t = setTimeout(() => setD(val), delay); return () => clearTimeout(t); }, [val, delay]);
  return d;
}

export default function SupplierDirectory() {
  const [data, setData]           = useState([]);
  const [total, setTotal]         = useState(0);
  const [page, setPage]           = useState(1);
  const pageSize = 15;
  const [loading, setLoading]     = useState(true);
  const [searchRaw, setSearchRaw] = useState('');
  const search = useDebounce(searchRaw, 350);
  const [statusFilter, setStatus] = useState('');
  const [selectedUid, setSelected] = useState(null);
  const [exporting, setExporting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listSuppliers({ status: statusFilter || undefined, search: search || undefined, page, pageSize });
      setData(res.data || []);
      setTotal(res.total || 0);
    } catch (_) {}
    setLoading(false);
  }, [search, statusFilter, page]);

  useEffect(() => { setPage(1); }, [search, statusFilter]);
  useEffect(() => { load(); }, [load]);

  async function doExport() {
    setExporting(true);
    try { await exportSuppliersCSV(); } catch (_) {}
    setExporting(false);
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 0 }}>
      {/* Toolbar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '16px 24px', borderBottom: '1px solid #F3F4F6', flexWrap: 'wrap',
      }}>
        {/* Search */}
        <div style={{ position: 'relative', flex: 1, minWidth: 220 }}>
          <Search size={14} color="#9CA3AF" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
          <input
            value={searchRaw} onChange={e => setSearchRaw(e.target.value)}
            placeholder="Search suppliers…"
            style={{
              width: '100%', paddingLeft: 34, paddingRight: 12, height: 36,
              border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 13,
              outline: 'none', boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Status Chips */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {STATUS_FILTERS.map(f => (
            <button key={f.value} onClick={() => setStatus(f.value)} style={{
              padding: '5px 12px', borderRadius: 999, fontSize: 12, fontWeight: 600,
              cursor: 'pointer', border: `1.5px solid ${statusFilter === f.value ? '#2563EB' : '#E5E7EB'}`,
              background: statusFilter === f.value ? '#EFF6FF' : 'white',
              color: statusFilter === f.value ? '#2563EB' : '#6B7280',
            }}>{f.label}</button>
          ))}
        </div>

        <button onClick={load} style={iconBtn} title="Refresh">
          <RefreshCw size={14} color="#6B7280" />
        </button>
        <button onClick={doExport} disabled={exporting} style={iconBtn} title="Export CSV">
          <Download size={14} color="#6B7280" />
          <span style={{ fontSize: 12, color: '#6B7280', fontWeight: 600 }}>CSV</span>
        </button>
      </div>

      {/* Count */}
      <div style={{ padding: '10px 24px 0', fontSize: 12, color: '#9CA3AF' }}>
        {total} supplier{total !== 1 ? 's' : ''} found
      </div>

      {/* Table */}
      <div style={{ flex: 1, overflowY: 'auto', overflowX: 'auto' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, gap: 10 }}>
            <RefreshCw size={18} color="#2563EB" style={{ animation: 'spin 1s linear infinite' }} />
            <span style={{ fontSize: 14, color: '#6B7280' }}>Loading…</span>
          </div>
        ) : data.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 24px' }}>
            <Building2 size={36} color="#E5E7EB" style={{ marginBottom: 12 }} />
            <p style={{ fontSize: 14, color: '#9CA3AF', fontWeight: 600 }}>No suppliers found</p>
            <p style={{ fontSize: 13, color: '#D1D5DB', marginTop: 4 }}>Invite suppliers to get started</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#F9FAFB', position: 'sticky', top: 0 }}>
                {['Company', 'Code', 'Contact', 'Country', 'Category', 'Status', 'Risk', 'Joined', ''].map(h => (
                  <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map(s => {
                const ss = STATUS_STYLE[s.status?.toUpperCase()] || { label: s.status || 'Pending', color: '#6B7280', bg: '#F3F4F6' };
                return (

                  <tr key={s.supabase_uid} style={{ borderBottom: '1px solid #F3F4F6' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#F9FAFB'}
                    onMouseLeave={e => e.currentTarget.style.background = 'white'}
                  >
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                          width: 32, height: 32, borderRadius: 8, background: '#EFF6FF',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, overflow: 'hidden',
                        }}>
                          {s.logo_url
                            ? <img src={s.logo_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            : <Building2 size={15} color="#2563EB" />}
                        </div>
                        <div>
                          <div style={{ fontWeight: 700, color: '#111827', whiteSpace: 'nowrap' }}>{s.company_name}</div>
                          <div style={{ fontSize: 11, color: '#9CA3AF' }}>{s.email}</div>
                        </div>
                        {s.is_critical && <span style={{ fontSize: 9, fontWeight: 800, color: '#EF4444', background: '#FEE2E2', padding: '2px 6px', borderRadius: 999 }}>CRIT</span>}
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#6B7280', whiteSpace: 'nowrap' }}>{s.supplier_code || '—'}</td>
                    <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                      <div style={{ fontWeight: 600, color: '#111827' }}>{s.contact_name}</div>
                      <div style={{ fontSize: 11, color: '#9CA3AF' }}>{s.phone}</div>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#374151', whiteSpace: 'nowrap' }}>
                      {[s.headquarters_city, s.headquarters_country].filter(Boolean).join(', ') || '—'}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#374151', whiteSpace: 'nowrap' }}>
                      {(s.manufacturing_categories || []).slice(0, 1).join(', ') || '—'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: ss.color, background: ss.bg, padding: '3px 10px', borderRadius: 999 }}>
                        {ss.label}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: RISK_COLOR[s.risk_rating] || '#9CA3AF' }}>
                        {s.risk_rating || 'UNKNOWN'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#9CA3AF', whiteSpace: 'nowrap', fontSize: 11 }}>
                      {s.created_at ? new Date(s.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <button onClick={() => setSelected(s.supabase_uid)} style={{
                        border: 'none', background: 'none', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', gap: 4, color: '#2563EB', fontSize: 12, fontWeight: 600,
                      }}>
                        <Eye size={13} /> View
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          padding: '12px 24px', borderTop: '1px solid #F3F4F6',
        }}>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={pageBtn}>
            <ChevronLeft size={14} />
          </button>
          <span style={{ fontSize: 13, color: '#374151', fontWeight: 600 }}>Page {page} of {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={pageBtn}>
            <ChevronRight size={14} />
          </button>
        </div>
      )}

      {/* Profile Drawer */}
      {selectedUid && (
        <SupplierProfileDrawer
          supplierUid={selectedUid}
          onClose={() => setSelected(null)}
          onActionComplete={load}
        />
      )}
    </div>
  );
}

const iconBtn = { display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 10px', borderRadius: 7, border: '1px solid #E5E7EB', background: 'white', cursor: 'pointer' };
const pageBtn = { padding: '5px 10px', borderRadius: 7, border: '1px solid #E5E7EB', background: 'white', cursor: 'pointer' };
