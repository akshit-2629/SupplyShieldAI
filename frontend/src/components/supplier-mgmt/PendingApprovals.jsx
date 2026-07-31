/**
 * PendingApprovals.jsx — Review and act on PENDING supplier registrations.
 */

import { useState, useEffect, useCallback } from 'react';
import { Clock, CheckCircle2, XCircle, FileText, Building2, Mail, Phone, Globe, RefreshCw, Eye } from 'lucide-react';
import { listSuppliers } from '../../services/supplierManagementApi';
import SupplierProfileDrawer from './SupplierProfileDrawer';

export default function PendingApprovals() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [selectedUid, setSelected] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listSuppliers({ status: 'PENDING', pageSize: 100 });
      setSuppliers(res.data || []);
    } catch (_) {}
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300, gap: 10 }}>
        <RefreshCw size={18} color="#2563EB" style={{ animation: 'spin 1s linear infinite' }} />
        <span style={{ fontSize: 14, color: '#6B7280' }}>Loading pending approvals…</span>
      </div>
    );
  }

  if (suppliers.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 24px' }}>
        <div style={{
          width: 64, height: 64, borderRadius: '50%', background: '#D1FAE5',
          display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px',
        }}>
          <CheckCircle2 size={30} color="#10B981" />
        </div>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: '#111827', marginBottom: 6 }}>All caught up!</h3>
        <p style={{ fontSize: 13, color: '#9CA3AF' }}>No supplier registrations are waiting for approval.</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #F3F4F6' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Clock size={16} color="#F59E0B" />
          <span style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>
            {suppliers.length} Pending Approval{suppliers.length !== 1 ? 's' : ''}
          </span>
        </div>
        <button onClick={load} style={iconBtn}>
          <RefreshCw size={13} color="#6B7280" />
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        {suppliers.map(s => (
          <div key={s.supabase_uid} style={{
            padding: '16px 24px', borderBottom: '1px solid #F3F4F6',
            display: 'flex', gap: 16, alignItems: 'flex-start',
          }}>
            {/* Logo */}
            <div style={{
              width: 44, height: 44, borderRadius: 10, background: '#FEF3C7',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}>
              {s.logo_url
                ? <img src={s.logo_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 10 }} />
                : <Building2 size={20} color="#F59E0B" />}
            </div>

            {/* Info */}
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                <span style={{ fontSize: 14, fontWeight: 800, color: '#111827' }}>{s.company_name}</span>
                {s.is_critical && <span style={{ fontSize: 10, fontWeight: 700, color: '#EF4444', background: '#FEE2E2', padding: '2px 7px', borderRadius: 999 }}>CRITICAL</span>}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, fontSize: 12, color: '#6B7280' }}>
                <span><Mail size={11} style={{ verticalAlign: 'middle', marginRight: 3 }} />{s.email}</span>
                {s.contact_name && <span><span style={{ fontWeight: 600 }}>{s.contact_name}</span></span>}
                {s.phone && <span><Phone size={11} style={{ verticalAlign: 'middle', marginRight: 3 }} />{s.phone}</span>}
                {s.headquarters_country && <span><Globe size={11} style={{ verticalAlign: 'middle', marginRight: 3 }} />{s.headquarters_country}</span>}
              </div>
              {(s.manufacturing_categories || []).length > 0 && (
                <div style={{ display: 'flex', gap: 5, marginTop: 6, flexWrap: 'wrap' }}>
                  {s.manufacturing_categories.slice(0, 3).map((c, i) => (
                    <span key={i} style={{ fontSize: 11, color: '#374151', background: '#F3F4F6', padding: '2px 8px', borderRadius: 999 }}>{c}</span>
                  ))}
                </div>
              )}
              <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 5 }}>
                Registered {s.created_at ? new Date(s.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : ''}
              </div>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: 8, flexShrink: 0, alignItems: 'center' }}>
              <button onClick={() => setSelected(s.supabase_uid)} style={{
                display: 'inline-flex', alignItems: 'center', gap: 5,
                padding: '7px 14px', borderRadius: 7,
                border: '1.5px solid #2563EB', background: '#EFF6FF',
                color: '#2563EB', fontSize: 12, fontWeight: 700, cursor: 'pointer',
              }}>
                <Eye size={13} /> Review
              </button>
            </div>
          </div>
        ))}
      </div>

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
