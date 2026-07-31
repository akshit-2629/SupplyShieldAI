/**
 * Step6Review.jsx — Read-only summary of all setup data (Setup Wizard, Step 6).
 * Shows company, factories, warehouses, products, components with edit-jump links.
 */

import { CheckCircle2, Building2, Factory, Warehouse, Package, Cpu, Pencil } from 'lucide-react';
import { useSetupStore } from '../../store/setupStore';

const CRIT_COLORS = { Low: '#10B981', Medium: '#F59E0B', High: '#F97316', Critical: '#EF4444' };

export default function Step6Review({ onNext, onBack, onJumpTo }) {
  const { company, factories, warehouses, products, components } = useSetupStore();

  const productName = (id) =>
    products.find((p) => p.id === id)?.product_name || null;

  return (
    <div style={{ maxWidth: 760, animation: 'slideUp 0.3s ease both' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: '#EFF6FF', border: '1px solid #DBEAFE',
          borderRadius: 20, padding: '4px 12px', marginBottom: 12,
        }}>
          <CheckCircle2 size={13} color="#2563EB" />
          <span style={{ fontSize: 12, fontWeight: 600, color: '#2563EB' }}>Step 6 of 7 — Review</span>
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#111827', marginBottom: 6 }}>
          Review Your Configuration
        </h1>
        <p style={{ fontSize: 14, color: '#6B7280' }}>
          Confirm all details before activating AI monitoring. Click any section to edit.
        </p>
      </div>

      {/* ── Company ── */}
      <ReviewCard
        icon={<Building2 size={16} color="#2563EB" />}
        title="Company Information"
        onEdit={() => onJumpTo(1)}
      >
        <Row label="Company"    value={company.name || '—'} />
        <Row label="Industry"   value={company.industry} />
        <Row label="Country"    value={[company.city, company.state, company.country].filter(Boolean).join(', ') || '—'} />
        <Row label="Email"      value={company.business_email || '—'} />
        <Row label="Phone"      value={company.business_phone || '—'} />
        <Row label="Website"    value={company.website || '—'} />
        <Row label="Size"       value={company.company_size || '—'} />
        <Row label="Capacity"   value={company.annual_production_cap || '—'} />
        <Row label="Timezone"   value={company.timezone} />
        <Row label="Work Days"  value={(company.working_days || []).join(', ') || '—'} />
        <Row label="Work Hours" value={`${company.working_hours_start} – ${company.working_hours_end}`} />
      </ReviewCard>

      {/* ── Factories ── */}
      <ReviewCard
        icon={<Factory size={16} color="#2563EB" />}
        title={`Factories (${factories.length})`}
        onEdit={() => onJumpTo(2)}
      >
        {factories.length === 0 ? (
          <span style={{ fontSize: 13, color: '#9CA3AF' }}>No factories added</span>
        ) : (
          factories.map((f) => (
            <div key={f.id} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 12px', background: '#F9FAFB', borderRadius: 8, marginBottom: 6,
            }}>
              <div>
                <span style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>{f.factory_name}</span>
                <span style={{ fontSize: 11, color: '#9CA3AF', marginLeft: 8 }}>{f.factory_code}</span>
              </div>
              <div style={{ fontSize: 12, color: '#6B7280' }}>
                {[f.city, f.country].filter(Boolean).join(', ')} · {f.factory_type}
                <span style={{
                  marginLeft: 8, fontSize: 11, fontWeight: 600,
                  color: f.operating_status === 'Operational' ? '#10B981' : '#F59E0B',
                }}>{f.operating_status}</span>
              </div>
            </div>
          ))
        )}
      </ReviewCard>

      {/* ── Warehouses ── */}
      <ReviewCard
        icon={<Warehouse size={16} color="#2563EB" />}
        title={`Warehouses (${warehouses.length})`}
        onEdit={() => onJumpTo(3)}
      >
        {warehouses.length === 0 ? (
          <span style={{ fontSize: 13, color: '#9CA3AF' }}>No warehouses added</span>
        ) : (
          warehouses.map((w) => (
            <div key={w.id} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 12px', background: '#F9FAFB', borderRadius: 8, marginBottom: 6,
            }}>
              <div>
                <span style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>{w.warehouse_name}</span>
                <span style={{ fontSize: 11, color: '#9CA3AF', marginLeft: 8 }}>{w.warehouse_code}</span>
                {w.temp_controlled && (
                  <span style={{ marginLeft: 6, fontSize: 10, color: '#2563EB', fontWeight: 600 }}>❄ Temp</span>
                )}
              </div>
              <div style={{ fontSize: 12, color: '#6B7280' }}>
                {[w.city, w.country].filter(Boolean).join(', ')} · {w.storage_capacity || '—'}
              </div>
            </div>
          ))
        )}
      </ReviewCard>

      {/* ── Products ── */}
      <ReviewCard
        icon={<Package size={16} color="#2563EB" />}
        title={`Products (${products.length})`}
        onEdit={() => onJumpTo(4)}
      >
        {products.length === 0 ? (
          <span style={{ fontSize: 13, color: '#9CA3AF' }}>No products defined</span>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {products.map((p) => (
              <div key={p.id} style={{
                background: 'white', border: '1px solid #E5E7EB', borderRadius: 8,
                padding: '8px 14px', minWidth: 160,
              }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>{p.product_name}</div>
                <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2 }}>
                  {p.sku} · {p.category}
                  {p.production_volume && ` · ${p.production_volume.toLocaleString()} units/mo`}
                </div>
              </div>
            ))}
          </div>
        )}
      </ReviewCard>

      {/* ── Components ── */}
      <ReviewCard
        icon={<Cpu size={16} color="#2563EB" />}
        title={`Components (${components.length})`}
        onEdit={() => onJumpTo(5)}
      >
        {components.length === 0 ? (
          <span style={{ fontSize: 13, color: '#9CA3AF' }}>No components defined</span>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {components.map((c) => (
              <div key={c.id} style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '7px 12px', background: '#F9FAFB', borderRadius: 8,
              }}>
                <div style={{
                  width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                  background: CRIT_COLORS[c.criticality] || '#E5E7EB',
                }} />
                <span style={{ fontSize: 13, fontWeight: 600, color: '#111827', flex: 1 }}>
                  {c.component_name}
                </span>
                <span style={{ fontSize: 11, color: '#6B7280' }}>
                  {c.category}
                  {c.product_id && ` · ${productName(c.product_id) || ''}`}
                </span>
                <span style={{ fontSize: 11, fontWeight: 700, color: CRIT_COLORS[c.criticality] }}>
                  {c.criticality}
                </span>
              </div>
            ))}
          </div>
        )}
      </ReviewCard>

      {/* Readiness banner */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 14,
        background: 'linear-gradient(135deg, #EFF6FF, #F0FDF4)',
        border: '1px solid #DBEAFE', borderRadius: 12, padding: '18px 22px', marginBottom: 28,
      }}>
        <CheckCircle2 size={24} color="#10B981" />
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>
            Configuration complete — ready to activate
          </div>
          <div style={{ fontSize: 12, color: '#6B7280', marginTop: 3 }}>
            {factories.length} factories · {warehouses.length} warehouses ·{' '}
            {products.length} products · {components.length} components
          </div>
        </div>
      </div>

      <NavRow onBack={onBack} onNext={onNext} />
    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────

function ReviewCard({ icon, title, onEdit, children }) {
  return (
    <div style={{
      background: 'white', border: '1px solid #E5E7EB', borderRadius: 12,
      padding: '20px 22px', marginBottom: 16,
    }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8, background: '#EFF6FF',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>{icon}</div>
          <span style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>{title}</span>
        </div>
        <button onClick={onEdit} style={{
          display: 'flex', alignItems: 'center', gap: 5,
          padding: '5px 12px', borderRadius: 7, border: '1px solid #E5E7EB',
          background: 'white', color: '#6B7280', fontSize: 12, fontWeight: 600, cursor: 'pointer',
        }}>
          <Pencil size={11} />Edit
        </button>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>{children}</div>
    </div>
  );
}

function Row({ label, value }) {
  if (!value || value === '—') return null;
  return (
    <div style={{
      display: 'flex', gap: 12, fontSize: 13,
      borderBottom: '1px solid #F3F4F6', paddingBottom: 6,
    }}>
      <span style={{ width: 140, flexShrink: 0, color: '#9CA3AF', fontWeight: 500 }}>{label}</span>
      <span style={{ color: '#111827', fontWeight: 500, wordBreak: 'break-word' }}>{value}</span>
    </div>
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
        padding: '11px 28px', borderRadius: 10, border: 'none',
        background: 'linear-gradient(135deg, #10B981, #059669)',
        color: 'white', fontSize: 14, fontWeight: 700, cursor: 'pointer',
        boxShadow: '0 4px 14px rgba(16,185,129,0.3)',
      }}>Activate AI Monitoring →</button>
    </div>
  );
}
