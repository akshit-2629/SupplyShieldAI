/**
 * SupplierManagement.jsx — Main Supplier Lifecycle Management page.
 *
 * Tab navigation across 6 sub-views:
 *  Directory | Pending Approvals | Invitations | Active | Suspended | Analytics
 *
 * Opens InviteSupplierModal from any tab via the global "Invite Supplier" button.
 */

import { useState, useEffect } from 'react';
import {
  Users, Clock, Send, CheckCircle2, Pause, BarChart2,
  UserPlus, ShieldCheck, Building2, RefreshCw,
} from 'lucide-react';
import { getSupplierAnalytics, listSuppliers } from '../services/supplierManagementApi';
import SupplierDirectory     from '../components/supplier-mgmt/SupplierDirectory';
import PendingApprovals      from '../components/supplier-mgmt/PendingApprovals';
import PendingInvitations    from '../components/supplier-mgmt/PendingInvitations';
import SupplierAnalytics     from '../components/supplier-mgmt/SupplierAnalytics';
import InviteSupplierModal   from '../components/supplier-mgmt/InviteSupplierModal';
import SupplierProfileDrawer from '../components/supplier-mgmt/SupplierProfileDrawer';

const TABS = [
  { id: 'directory',  label: 'All Suppliers',     icon: Users,        badge: null },
  { id: 'pending',    label: 'Pending Approvals', icon: Clock,        badge: 'pending_approval', badgeColor: '#F59E0B' },
  { id: 'invitations',label: 'Invitations',       icon: Send,         badge: 'pending_invitations', badgeColor: '#2563EB' },
  { id: 'active',     label: 'Active',            icon: CheckCircle2, badge: 'active_suppliers', badgeColor: '#10B981' },
  { id: 'suspended',  label: 'Suspended',         icon: Pause,        badge: 'suspended_suppliers', badgeColor: '#6B7280' },
  { id: 'analytics',  label: 'Analytics',         icon: BarChart2,    badge: null },
];

export default function SupplierManagement() {
  const [activeTab, setActiveTab]     = useState('directory');
  const [showInvite, setShowInvite]   = useState(false);
  const [analytics, setAnalytics]     = useState(null);
  const [inviteKey, setInviteKey]     = useState(0); // force re-render of invitations tab after invite

  // Load analytics summary for badge counts
  useEffect(() => {
    getSupplierAnalytics().then(setAnalytics).catch(() => {});
  }, [inviteKey]);

  function handleInviteSuccess() {
    setShowInvite(false);
    setInviteKey(k => k + 1);
    setActiveTab('invitations');
    // Refresh analytics
    getSupplierAnalytics().then(setAnalytics).catch(() => {});
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: '#F8FAFF', minHeight: '100vh',
    }}>

      {/* ── Page Header ── */}
      <div style={{
        background: 'white', borderBottom: '1px solid #E5E7EB',
        padding: '20px 28px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 12,
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <ShieldCheck size={18} color="white" />
            </div>
            <div>
              <h1 style={{ fontSize: 18, fontWeight: 800, color: '#111827', margin: 0, lineHeight: 1.2 }}>
                Supplier Management
              </h1>
              <p style={{ fontSize: 12, color: '#6B7280', margin: 0, marginTop: 2 }}>
                Invite, onboard, approve, and manage your supplier network
              </p>
            </div>
          </div>
        </div>

        {/* Top-right KPI chips + invite button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {analytics && (
            <>
              <Chip label="Active"   value={analytics.active_suppliers}   color="#10B981" />
              <Chip label="Pending"  value={analytics.pending_approval}   color="#F59E0B" />
              <Chip label="Critical" value={analytics.critical_suppliers} color="#EF4444" />
            </>
          )}
          <button
            onClick={() => setShowInvite(true)}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              padding: '9px 18px', borderRadius: 9, border: 'none',
              background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
              color: 'white', fontSize: 13, fontWeight: 700, cursor: 'pointer',
              boxShadow: '0 2px 10px rgba(37,99,235,0.3)',
            }}
          >
            <UserPlus size={15} />
            Invite Supplier
          </button>
        </div>
      </div>

      {/* ── Tab Bar ── */}
      <div style={{
        background: 'white', borderBottom: '1px solid #E5E7EB',
        display: 'flex', overflowX: 'auto', padding: '0 20px',
      }}>
        {TABS.map(tab => {
          const Icon  = tab.icon;
          const count = analytics && tab.badge ? analytics[tab.badge] : null;
          const active = activeTab === tab.id;
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              display: 'flex', alignItems: 'center', gap: 7,
              padding: '13px 16px', fontSize: 13,
              fontWeight: active ? 700 : 500,
              color: active ? '#2563EB' : '#6B7280',
              borderBottom: active ? '2px solid #2563EB' : '2px solid transparent',
              background: 'none', border: 'none',
              borderBottom: active ? '2px solid #2563EB' : '2px solid transparent',
              cursor: 'pointer', whiteSpace: 'nowrap', flexShrink: 0,
              transition: 'color 0.15s',
            }}>
              <Icon size={14} />
              {tab.label}
              {count != null && count > 0 && (
                <span style={{
                  fontSize: 10, fontWeight: 800,
                  color: 'white',
                  background: tab.badgeColor || '#6B7280',
                  minWidth: 18, height: 18,
                  borderRadius: 999, padding: '0 5px',
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {count > 99 ? '99+' : count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Tab Content ── */}
      <div style={{ flex: 1, overflowY: 'auto', background: 'white', margin: '16px', borderRadius: 12, border: '1px solid #E5E7EB' }}>
        {activeTab === 'directory' && (
          <SupplierDirectory key={`dir-${inviteKey}`} />
        )}
        {activeTab === 'pending' && (
          <PendingApprovals key={`pend-${inviteKey}`} />
        )}
        {activeTab === 'invitations' && (
          <PendingInvitations
            key={`inv-${inviteKey}`}
            onInvite={() => setShowInvite(true)}
          />
        )}
        {activeTab === 'active' && (
          <ActiveSuppliersView key={`act-${inviteKey}`} />
        )}
        {activeTab === 'suspended' && (
          <SuspendedSuppliersView key={`sus-${inviteKey}`} />
        )}
        {activeTab === 'analytics' && (
          <SupplierAnalytics key={`ana-${inviteKey}`} />
        )}
      </div>

      {/* ── Invite Modal ── */}
      {showInvite && (
        <InviteSupplierModal
          onClose={() => setShowInvite(false)}
          onSuccess={handleInviteSuccess}
        />
      )}
    </div>
  );
}

// ── Thin wrappers for Active / Suspended (pass status filter to directory) ────

function ActiveSuppliersView() {
  return <FilteredDirectory status="APPROVED" emptyLabel="No active suppliers yet" emptyIcon={CheckCircle2} />;
}

function SuspendedSuppliersView() {
  return <FilteredDirectory status="SUSPENDED" emptyLabel="No suspended suppliers" emptyIcon={Pause} />;
}

function FilteredDirectory({ status, emptyLabel, emptyIcon: EmptyIcon }) {
  const [data, setData]       = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUid, setSelected] = useState(null);

  async function load() {
    setLoading(true);
    try {
      const res = await listSuppliers({ status, pageSize: 100 });
      setData(res.data || []);
    } catch (_) {}
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  const STATUS_STYLE = {
    APPROVED:  { label: 'Active',    color: '#10B981', bg: '#D1FAE5' },
    SUSPENDED: { label: 'Suspended', color: '#6B7280', bg: '#F3F4F6' },
  };

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, gap: 10 }}>
      <RefreshCw size={18} color="#2563EB" style={{ animation: 'spin 1s linear infinite' }} />
    </div>
  );

  if (data.length === 0) return (
    <div style={{ textAlign: 'center', padding: '60px 24px' }}>
      <EmptyIcon size={32} color="#E5E7EB" style={{ marginBottom: 12 }} />
      <p style={{ fontSize: 14, color: '#9CA3AF', fontWeight: 600 }}>{emptyLabel}</p>
    </div>
  );

  const ss = STATUS_STYLE[status];

  return (
    <div>
      <div style={{ padding: '14px 24px', borderBottom: '1px solid #F3F4F6', fontSize: 12, color: '#9CA3AF' }}>
        {data.length} supplier{data.length !== 1 ? 's' : ''}
      </div>
      {data.map(s => (
        <div key={s.supabase_uid} style={{
          display: 'flex', alignItems: 'center', gap: 14, padding: '14px 24px',
          borderBottom: '1px solid #F3F4F6', cursor: 'pointer',
        }}
          onClick={() => setSelected(s.supabase_uid)}
          onMouseEnter={e => e.currentTarget.style.background = '#F9FAFB'}
          onMouseLeave={e => e.currentTarget.style.background = 'white'}
        >
          <div style={{
            width: 36, height: 36, borderRadius: 9, background: '#F3F4F6',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, overflow: 'hidden',
          }}>
            {s.logo_url
              ? <img src={s.logo_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              : <Building2 size={16} color="#9CA3AF" />}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>{s.company_name}</span>
              {s.is_critical && <span style={{ fontSize: 9, fontWeight: 800, color: '#EF4444', background: '#FEE2E2', padding: '1px 6px', borderRadius: 999 }}>CRIT</span>}
              <span style={{ fontSize: 11, color: '#9CA3AF' }}>{s.supplier_code}</span>
            </div>
            <div style={{ fontSize: 12, color: '#6B7280', marginTop: 2 }}>
              {s.contact_name} · {s.email}
              {s.headquarters_country ? ` · ${s.headquarters_country}` : ''}
            </div>
          </div>
          <span style={{ fontSize: 11, fontWeight: 700, color: ss?.color, background: ss?.bg, padding: '3px 10px', borderRadius: 999 }}>
            {ss?.label}
          </span>
        </div>
      ))}
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

function Chip({ label, value, color }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      background: 'white', border: '1px solid #E5E7EB',
      borderRadius: 8, padding: '5px 12px',
    }}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: color, display: 'inline-block' }} />
      <span style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 800, color: '#111827' }}>{value ?? '—'}</span>
    </div>
  );
}
