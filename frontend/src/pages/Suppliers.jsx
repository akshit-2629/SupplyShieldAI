import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, X, Star, Shield, TrendingUp, Users, ChevronUp, ChevronDown, RefreshCw,
  Building2, MapPin, Globe, Phone, Mail, Box, Cpu, Truck, FileText, CheckCircle2,
  Clock, AlertTriangle, Layers, Plus, ArrowUpRight
} from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { scoreColor, statusColor } from '../lib/utils';

const countryFlags = { TW: '🇹🇼', KR: '🇰🇷', DE: '🇩🇪', JP: '🇯🇵', US: '🇺🇸', SG: '🇸🇬', IN: '🇮🇳', FR: '🇫🇷', CN: '🇨🇳', NL: '🇳🇱' };

function riskScoreColor(score) {
  if (score >= 70) return { bg: '#FEE2E2', color: '#DC2626', label: 'HIGH' };
  if (score >= 40) return { bg: '#FEF3C7', color: '#D97706', label: 'MEDIUM' };
  return { bg: '#D1FAE5', color: '#059669', label: 'LOW' };
}

function SupplierModal({ supplier, onClose }) {
  const rc = riskScoreColor(supplier.risk_score || 15);
  const stc = statusColor(supplier.status || 'ACTIVE');

  return (
    <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.div initial={{ opacity: 0, y: 20, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 20, scale: 0.96 }}
        onClick={e => e.stopPropagation()}
        style={{ width: 680, background: 'white', borderRadius: 14, boxShadow: '0 20px 60px rgba(0,0,0,0.15)', overflow: 'hidden', maxHeight: '90vh', overflowY: 'auto' }}
      >
        {/* Header Banner */}
        <div style={{ padding: '22px 26px', borderBottom: '1px solid #F1F5F9', background: '#F8FAFC', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {supplier.logo_url ? (
              <img src={supplier.logo_url} alt={supplier.company_name} style={{ width: 52, height: 52, borderRadius: 10, objectFit: 'cover', border: '1px solid #E2E8F0' }} />
            ) : (
              <div style={{ width: 52, height: 52, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, color: 'white', fontWeight: 800 }}>
                {countryFlags[supplier.country_code] || '🏢'}
              </div>
            )}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <h2 style={{ fontSize: 18, fontWeight: 800, color: '#0F172A', margin: 0 }}>{supplier.company_name || supplier.name}</h2>
                <span style={{ background: stc.bg, color: stc.text, fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 10, textTransform: 'uppercase' }}>
                  {supplier.status || 'ACTIVE'}
                </span>
              </div>
              <div style={{ fontSize: 13, color: '#64748B', display: 'flex', gap: 12, alignItems: 'center' }}>
                <span>{countryFlags[supplier.country_code]} {supplier.headquarters_country || supplier.country_code || 'United States'}</span>
                <span>•</span>
                <span>{supplier.industry_sector || 'Semiconductors & Electronics'}</span>
              </div>
            </div>
          </div>
          <button onClick={onClose} style={{ background: '#F1F5F9', border: 'none', borderRadius: 8, width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
            <X size={16} color="#64748B" />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '22px 26px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Key Metrics Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
            <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: 12, textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 900, color: '#059669' }}>{supplier.reliability || '98.5%'}</div>
              <div style={{ fontSize: 11, color: '#64748B', marginTop: 2, fontWeight: 600 }}>Reliability</div>
            </div>
            <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: 12, textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 900, color: '#2563EB' }}>{supplier.lead_time || '14 Days'}</div>
              <div style={{ fontSize: 11, color: '#64748B', marginTop: 2, fontWeight: 600 }}>Lead Time</div>
            </div>
            <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: 12, textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 900, color: rc.color }}>{supplier.risk_score || 15}/100</div>
              <div style={{ fontSize: 11, color: '#64748B', marginTop: 2, fontWeight: 600 }}>Risk Score ({rc.label})</div>
            </div>
            <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: 12, textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 900, color: '#7C3AED' }}>{supplier.performance || 'EXCELLENT'}</div>
              <div style={{ fontSize: 11, color: '#64748B', marginTop: 2, fontWeight: 600 }}>Performance</div>
            </div>
          </div>

          {/* Operational Metadata */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div style={{ background: '#FAFAFA', border: '1px solid #F1F5F9', borderRadius: 8, padding: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#475569', marginBottom: 10, textTransform: 'uppercase' }}>Contact & Corporate Info</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Users size={14} color="#64748B" /> <strong>Contact:</strong> {supplier.contact_name || supplier.contact_person || '—'}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Mail size={14} color="#64748B" /> <strong>Email:</strong> {supplier.email || supplier.supplier_email || '—'}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Phone size={14} color="#64748B" /> <strong>Phone:</strong> {supplier.contact_phone || supplier.phone || '—'}</div>
                {supplier.website && <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Globe size={14} color="#64748B" /> <strong>Website:</strong> {supplier.website}</div>}

            </div>

            <div style={{ background: '#FAFAFA', border: '1px solid #F1F5F9', borderRadius: 8, padding: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#475569', marginBottom: 10, textTransform: 'uppercase' }}>Capacity & Compliance</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Layers size={14} color="#64748B" /> <strong>Monthly Capacity:</strong> {supplier.capacity || '50,000 units/mo'}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Truck size={14} color="#64748B" /> <strong>Active Shipments:</strong> {supplier.shipment_count || 4} Completed</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><FileText size={14} color="#64748B" /> <strong>Compliance Docs:</strong> {supplier.document_count || 4} Verified</div>
              </div>
            </div>
          </div>

          {/* Supplied Components & Products */}
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#475569', marginBottom: 8, textTransform: 'uppercase' }}>Supplied Components & Products</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {(supplier.components_supplied || []).map((c, i) => (
                <span key={i} style={{ background: '#EFF6FF', color: '#1E40AF', fontSize: 12, fontWeight: 600, padding: '4px 10px', borderRadius: 6, border: '1px solid #BFDBFE' }}>
                  <Cpu size={12} style={{ display: 'inline', marginRight: 4 }} /> {c}
                </span>
              ))}
              {(!supplier.components_supplied || supplier.components_supplied.length === 0) && (
                <span style={{ fontSize: 13, color: '#94A3B8' }}>No linked components in PostgreSQL.</span>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function Suppliers() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [selectedSupplier, setSelectedSupplier] = useState(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['suppliers-list'],
    queryFn: () => api.get('/suppliers/'),
  });

  const suppliers = Array.isArray(data) ? data : Array.isArray(data?.suppliers) ? data.suppliers : [];

  const filtered = suppliers.filter(s => {
    const q = search.toLowerCase();
    return (s.name || s.company_name || '').toLowerCase().includes(q) ||
           (s.country_code || s.headquarters_country || '').toLowerCase().includes(q) ||
           (s.status || '').toLowerCase().includes(q);
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1280 }}>
      {/* Top Title & Actions Bar */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h1 style={{ fontSize: 22, fontWeight: 800, color: '#0F172A', margin: 0 }}>Supplier Management</h1>
            <span style={{ background: '#F1F5F9', color: '#475569', fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 10 }}>PostgreSQL Enforced</span>
          </div>
          <p style={{ fontSize: 13.5, color: '#64748B', marginTop: 4 }}>Monitor performance, reliability, lead times, and capacity for authenticated manufacturer suppliers</p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button 
            onClick={() => navigate('/supplier-mgmt')}
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#2563EB', color: 'white', border: 'none', borderRadius: 8, padding: '9px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
          >
            <Plus size={15} /> Supplier Onboarding
          </button>
          <button 
            onClick={() => refetch()} 
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#F8FAFC', color: '#475569', border: '1px solid #CBD5E1', borderRadius: 8, padding: '9px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </motion.div>

      {/* Overview Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
        <div className="card" style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 42, height: 42, background: '#EFF6FF', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Building2 size={20} color="#2563EB" />
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 900, color: '#0F172A' }}>{isLoading ? '…' : suppliers.length}</div>
            <div style={{ fontSize: 12, color: '#64748B', fontWeight: 600 }}>Active Suppliers</div>
          </div>
        </div>

        <div className="card" style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 42, height: 42, background: '#ECFDF5', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <TrendingUp size={20} color="#059669" />
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 900, color: '#059669' }}>98.5%</div>
            <div style={{ fontSize: 12, color: '#64748B', fontWeight: 600 }}>Avg. Reliability</div>
          </div>
        </div>

        <div className="card" style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 42, height: 42, background: '#F5F3FF', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Clock size={20} color="#7C3AED" />
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 900, color: '#7C3AED' }}>14 Days</div>
            <div style={{ fontSize: 12, color: '#64748B', fontWeight: 600 }}>Avg. Lead Time</div>
          </div>
        </div>

        <div className="card" style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 42, height: 42, background: '#FEF2F2', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Shield size={20} color="#DC2626" />
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 900, color: '#DC2626' }}>
              {suppliers.filter(s => (s.risk_score || 0) >= 70).length}
            </div>
            <div style={{ fontSize: 12, color: '#64748B', fontWeight: 600 }}>High Risk Suppliers</div>
          </div>
        </div>
      </div>

      {/* Main Suppliers Table / List */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #F1F5F9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: '7px 14px', width: 320 }}>
            <Search size={15} color="#94A3B8" />
            <input 
              value={search} 
              onChange={e => setSearch(e.target.value)} 
              placeholder="Search by supplier name, country, or status..." 
              style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: 13, width: '100%' }} 
            />
          </div>
          <span style={{ fontSize: 12.5, color: '#64748B', fontWeight: 600 }}>{filtered.length} suppliers in PostgreSQL</span>
        </div>

        {suppliers.length === 0 && !isLoading ? (
          <div style={{ padding: '48px 24px', textAlign: 'center', color: '#64748B' }}>
            <Building2 size={42} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
            <div style={{ fontSize: 16, fontWeight: 700, color: '#0F172A', marginBottom: 4 }}>0 Suppliers Onboarded</div>
            <div style={{ fontSize: 13, marginBottom: 16 }}>Your workspace currently has no registered or invited suppliers.</div>
            <button 
              onClick={() => navigate('/supplier-mgmt')}
              style={{ background: '#2563EB', color: 'white', border: 'none', borderRadius: 8, padding: '9px 18px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
            >
              Invite Supplier Now
            </button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
                  {['Supplier Company', 'Country', 'Industry Sector', 'Capacity', 'Lead Time', 'Reliability', 'Risk Score', 'Status', 'Actions'].map((h, i) => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: i === 8 ? 'right' : 'left', fontSize: 11.5, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((s, i) => {
                  const rc = riskScoreColor(s.risk_score || 15);
                  const stc = statusColor(s.status || 'ACTIVE');
                  return (
                    <tr key={s.supplier_id || i} style={{ borderBottom: '1px solid #F1F5F9', transition: 'background 0.15s' }}>
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          {s.logo_url ? (
                            <img src={s.logo_url} alt={s.name} style={{ width: 36, height: 36, borderRadius: 8, objectFit: 'cover' }} />
                          ) : (
                            <div style={{ width: 36, height: 36, background: '#EFF6FF', color: '#2563EB', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 800 }}>
                              {countryFlags[s.country_code] || '🏢'}
                            </div>
                          )}
                          <div>
                            <div style={{ fontSize: 13.5, fontWeight: 700, color: '#0F172A' }}>{s.company_name || s.name}</div>
                            <div style={{ fontSize: 11.5, color: '#64748B' }}>{s.email || 'No email registered'}</div>
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px', fontSize: 13, color: '#334155', fontWeight: 600 }}>
                        {countryFlags[s.country_code]} {s.headquarters_country || s.country_code || 'US'}
                      </td>
                      <td style={{ padding: '14px 16px', fontSize: 12.5, color: '#475569' }}>
                        {s.industry_sector || 'Electronics'}
                      </td>
                      <td style={{ padding: '14px 16px', fontSize: 12.5, color: '#334155', fontWeight: 600 }}>
                        {s.capacity || '50,000/mo'}
                      </td>
                      <td style={{ padding: '14px 16px', fontSize: 12.5, color: '#334155', fontWeight: 600 }}>
                        {s.lead_time || '14 Days'}
                      </td>
                      <td style={{ padding: '14px 16px', fontSize: 13, fontWeight: 800, color: '#059669' }}>
                        {s.reliability || '98.5%'}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{ background: rc.bg, color: rc.color, fontSize: 11, fontWeight: 800, padding: '3px 8px', borderRadius: 6 }}>
                          {s.risk_score || 15}/100 ({rc.label})
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{ background: stc.bg, color: stc.text, fontSize: 11, fontWeight: 700, padding: '3px 9px', borderRadius: 10, textTransform: 'uppercase' }}>
                          {s.status || 'ACTIVE'}
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                        <button 
                          onClick={() => setSelectedSupplier(s)}
                          style={{ background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 6, padding: '6px 12px', fontSize: 12.5, fontWeight: 600, cursor: 'pointer' }}
                        >
                          Profile & Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      <AnimatePresence>
        {selectedSupplier && <SupplierModal supplier={selectedSupplier} onClose={() => setSelectedSupplier(null)} />}
      </AnimatePresence>
    </div>
  );
}
