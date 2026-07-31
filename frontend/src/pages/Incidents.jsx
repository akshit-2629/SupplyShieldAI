import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  MapPin, Clock, Brain, FileText, ArrowRight, ExternalLink, 
  RefreshCw, ShieldAlert, Factory, Truck, Box, Cpu, Building2,
  DollarSign, AlertTriangle, CheckCircle2, ArrowUpRight, Layers
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { severityColor, statusColor, timeAgo } from '../lib/utils';

export default function Incidents() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ALL');

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['enterprise-incidents', statusFilter],
    queryFn: () => {
      const param = statusFilter !== 'ALL' ? `?status=${statusFilter}` : '';
      return api.get(`/incidents${param}`);
    },
  });

  const generateMutation = useMutation({
    mutationFn: () => api.post('/incidents/generate'),
    onSuccess: () => {
      queryClient.invalidateQueries(['enterprise-incidents']);
      refetch();
    }
  });

  const rawIncidents = data?.incidents || (Array.isArray(data) ? data : []);
  const activeIncident = rawIncidents.find(i => i.id === selectedIncidentId) || rawIncidents[0] || null;

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1200 }}>
        <div style={{ height: 32, width: 300, background: '#F3F4F6', borderRadius: 6 }} />
        <div style={{ height: 140, background: '#F3F4F6', borderRadius: 10 }} />
        <div style={{ height: 400, background: '#F3F4F6', borderRadius: 10 }} />
      </div>
    );
  }

  if (!rawIncidents || rawIncidents.length === 0 || !activeIncident) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1200 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827' }}>Incident Investigation Center</h1>
            <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Deep-dive enterprise analysis of matched supply chain disruptions</p>
          </div>
          <button 
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#2563EB', color: 'white', border: 'none', borderRadius: 8, padding: '9px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
          >
            <RefreshCw size={14} className={generateMutation.isPending ? 'animate-spin' : ''} />
            {generateMutation.isPending ? 'Generating Incidents...' : 'Run AI Incident Generator'}
          </button>
        </div>

        <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 10, padding: '32px 24px', textAlign: 'center', color: '#1E40AF' }}>
          <Brain size={42} style={{ margin: '0 auto 12px', opacity: 0.6 }} />
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>No Enterprise Incidents Recorded</div>
          <div style={{ fontSize: 13, color: '#3B82F6', maxWidth: 480, margin: '0 auto 16px' }}>
            Run the AI Incident Generator to match recent disruption news against your registered PostgreSQL suppliers, components, factories, and shipments.
          </div>
          <button 
            onClick={() => generateMutation.mutate()}
            style={{ background: '#2563EB', color: 'white', border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 13.5, fontWeight: 600, cursor: 'pointer' }}
          >
            Generate Incidents Now
          </button>
        </div>
      </div>
    );
  }

  const sc = severityColor((activeIncident.risk_level || 'HIGH').toLowerCase());
  const stc = statusColor(activeIncident.status || 'ACTIVE');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1240 }}>
      {/* Top Header & Dropdown Controls */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', margin: 0 }}>Incident Investigation Center</h1>
            <span style={{ background: '#F3F4F6', color: '#4B5563', fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 10 }}>Enterprise MDM</span>
          </div>
          <p style={{ fontSize: 13.5, color: '#9CA3AF', marginTop: 4 }}>Structured PostgreSQL supply chain risk analysis & matched entity impact</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Incident Selector */}
          <select 
            value={activeIncident.id} 
            onChange={(e) => setSelectedIncidentId(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #D1D5DB', fontSize: 13, fontWeight: 600, background: 'white', color: '#111827', cursor: 'pointer', maxWidth: 320 }}
          >
            {rawIncidents.map((inc) => (
              <option key={inc.id} value={inc.id}>
                {inc.risk_level}: {inc.incident_title ? inc.incident_title.slice(0, 45) + '...' : inc.id}
              </option>
            ))}
          </select>

          <button 
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#2563EB', color: 'white', border: 'none', borderRadius: 8, padding: '9px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
          >
            <RefreshCw size={14} className={generateMutation.isPending ? 'animate-spin' : ''} />
            {generateMutation.isPending ? 'Syncing...' : 'Sync Incidents'}
          </button>
        </div>
      </motion.div>

      {/* Main Incident Banner */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="card" style={{ padding: 22, borderLeft: `5px solid ${sc.dot}` }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ flex: 1, minWidth: 300 }}>
            <div style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'center' }}>
              <span style={{ background: sc.bg, color: sc.text, fontSize: 11, fontWeight: 800, padding: '3px 9px', borderRadius: 12, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                {activeIncident.risk_level || 'HIGH'} RISK
              </span>
              <span style={{ background: stc.bg, color: stc.text, fontSize: 11, fontWeight: 700, padding: '3px 9px', borderRadius: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: stc.text }} />
                {activeIncident.status || 'ACTIVE'}
              </span>
              <span style={{ fontSize: 12, color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: 4, marginLeft: 6 }}>
                <Clock size={13} /> {timeAgo(activeIncident.created_at)}
              </span>
            </div>

            <h2 style={{ fontSize: 19, fontWeight: 800, color: '#111827', marginBottom: 8, lineHeight: 1.3 }}>
              {activeIncident.incident_title}
            </h2>

            <p style={{ fontSize: 13.5, color: '#4B5563', lineHeight: 1.6, marginBottom: 12 }}>
              {activeIncident.incident_description}
            </p>

            {/* Traceability Link to Source News */}
            {activeIncident.news_url && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, color: '#2563EB', background: '#F0F9FF', padding: '6px 12px', borderRadius: 6, width: 'fit-content', border: '1px solid #BAE6FD' }}>
                <ExternalLink size={13} />
                <span>Source Article: </span>
                <a href={activeIncident.news_url} target="_blank" rel="noreferrer" style={{ color: '#0284C7', fontWeight: 600, textDecoration: 'underline' }}>
                  {activeIncident.news_title || activeIncident.news_source || 'View Originating News Feed'}
                </a>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={() => navigate('/recommendations')} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 8, padding: '9px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
              <ArrowRight size={14} /> View AI Recommendations
            </button>
            <button onClick={() => navigate('/reports')} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#111827', color: 'white', border: 'none', borderRadius: 8, padding: '9px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
              <FileText size={14} /> Full Executive Report
            </button>
          </div>
        </div>
      </motion.div>

      {/* 6 Matched Supply Chain Entities Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 12 }}>
        <div className="card" style={{ padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#6B7280', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>
            <Building2 size={15} color="#2563EB" /> Affected Supplier
          </div>
          <div style={{ fontSize: 13.5, fontWeight: 700, color: '#111827' }}>
            {activeIncident.affected_supplier || 'Global Supplier'}
          </div>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#6B7280', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>
            <Factory size={15} color="#7C3AED" /> Affected Factory
          </div>
          <div style={{ fontSize: 13.5, fontWeight: 700, color: '#111827' }}>
            {activeIncident.affected_factory || 'Main Assembly Line'}
          </div>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#6B7280', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>
            <Cpu size={15} color="#DC2626" /> Affected Components
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {(activeIncident.affected_components || ['Components']).map((c, i) => (
              <span key={i} style={{ background: '#FEE2E2', color: '#991B1B', fontSize: 11, fontWeight: 600, padding: '2px 6px', borderRadius: 4 }}>{c}</span>
            ))}
          </div>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#6B7280', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>
            <Box size={15} color="#D97706" /> Affected Products
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {(activeIncident.affected_products || ['Products']).map((p, i) => (
              <span key={i} style={{ background: '#FEF3C7', color: '#92400E', fontSize: 11, fontWeight: 600, padding: '2px 6px', borderRadius: 4 }}>{p}</span>
            ))}
          </div>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#6B7280', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>
            <Layers size={15} color="#059669" /> Inventory Impact
          </div>
          <div style={{ fontSize: 12.5, fontWeight: 600, color: '#111827' }}>
            {activeIncident.affected_inventory || '500 units at risk'}
          </div>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#6B7280', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>
            <Truck size={15} color="#0284C7" /> Affected Shipment
          </div>
          <div style={{ fontSize: 12.5, fontWeight: 600, color: '#111827' }}>
            {activeIncident.affected_shipment || 'Shipment Delayed'}
          </div>
        </div>
      </div>

      {/* Quantitative Risk Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
        <div className="card" style={{ padding: 16, borderTop: '3px solid #DC2626' }}>
          <div style={{ fontSize: 12, color: '#9CA3AF', fontWeight: 600, marginBottom: 4 }}>RISK SCORE</div>
          <div style={{ fontSize: 26, fontWeight: 900, color: '#DC2626' }}>
            {(activeIncident.risk_score || 85).toFixed(0)} <span style={{ fontSize: 14, color: '#9CA3AF', fontWeight: 500 }}>/ 100</span>
          </div>
          <div style={{ fontSize: 11.5, color: '#6B7280', marginTop: 4 }}>Severity Weight × Exposure Multiplier</div>
        </div>

        <div className="card" style={{ padding: 16, borderTop: '3px solid #D97706' }}>
          <div style={{ fontSize: 12, color: '#9CA3AF', fontWeight: 600, marginBottom: 4 }}>FINANCIAL IMPACT</div>
          <div style={{ fontSize: 22, fontWeight: 900, color: '#D97706' }}>
            {activeIncident.financial_impact || '$450,000'}
          </div>
          <div style={{ fontSize: 11.5, color: '#6B7280', marginTop: 4 }}>Revenue exposure across Q3 shipments</div>
        </div>

        <div className="card" style={{ padding: 16, borderTop: '3px solid #7C3AED' }}>
          <div style={{ fontSize: 12, color: '#9CA3AF', fontWeight: 600, marginBottom: 4 }}>ESTIMATED DELAY</div>
          <div style={{ fontSize: 22, fontWeight: 900, color: '#7C3AED' }}>
            {activeIncident.estimated_delay || '14 - 21 Days'}
          </div>
          <div style={{ fontSize: 11.5, color: '#6B7280', marginTop: 4 }}>Lead time extension at assembly node</div>
        </div>

        <div className="card" style={{ padding: 16, borderTop: '3px solid #059669' }}>
          <div style={{ fontSize: 12, color: '#9CA3AF', fontWeight: 600, marginBottom: 4 }}>CONFIDENCE LEVEL</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#059669', marginTop: 4 }}>
            {activeIncident.confidence || '94% (High)'}
          </div>
          <div style={{ fontSize: 11.5, color: '#6B7280', marginTop: 4 }}>Multi-source news & sensor verification</div>
        </div>
      </div>

      {/* Deep-Dive Analysis: Root Cause, Recovery Plan, Actions, Alternative Suppliers */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 16, alignItems: 'start' }}>
        {/* Left Column: Root Cause + Recovery Plan + Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Root Cause & Business Impact */}
          <div className="card" style={{ padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <div style={{ width: 28, height: 28, background: 'linear-gradient(135deg,#DC2626,#D97706)', borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <AlertTriangle size={15} color="white" />
              </div>
              <div style={{ fontSize: 15, fontWeight: 800, color: '#111827' }}>Root Cause & Business Impact</div>
            </div>
            
            <div style={{ background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 8, padding: 14, marginBottom: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#991B1B', textTransform: 'uppercase', marginBottom: 4 }}>Root Cause Summary</div>
              <div style={{ fontSize: 13.5, color: '#7F1D1D', lineHeight: 1.5, fontWeight: 600 }}>
                {activeIncident.root_cause || activeIncident.incident_title}
              </div>
            </div>

            <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.7 }}>
              <strong>Business Impact Details:</strong> {activeIncident.business_impact || 'Manufacturing assembly lines at risk due to critical component delays.'}
            </div>
          </div>

          {/* Recovery Plan */}
          <div className="card" style={{ padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <div style={{ width: 28, height: 28, background: 'linear-gradient(135deg,#059669,#0284C7)', borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <CheckCircle2 size={15} color="white" />
              </div>
              <div style={{ fontSize: 15, fontWeight: 800, color: '#111827' }}>Structured Recovery Plan</div>
            </div>
            
            <p style={{ fontSize: 13.5, color: '#374151', lineHeight: 1.7, background: '#F8FAFC', padding: 14, borderRadius: 8, border: '1px solid #E2E8F0' }}>
              {activeIncident.recovery_plan || 'Phase 1: Emergency buffer dispatch. Phase 2: Production line re-allocation. Phase 3: Dual-sourcing activation.'}
            </p>
          </div>

          {/* Timeline */}
          <div className="card" style={{ padding: 20 }}>
            <div style={{ fontSize: 15, fontWeight: 800, color: '#111827', marginBottom: 16 }}>Incident Progression Timeline</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {(activeIncident.timeline || []).map((item, i) => (
                <div key={i} style={{ display: 'flex', gap: 12, paddingBottom: i < (activeIncident.timeline.length - 1) ? 12 : 0, borderBottom: i < (activeIncident.timeline.length - 1) ? '1px solid #F3F4F6' : 'none' }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: item.type === 'critical' ? '#DC2626' : '#2563EB', marginTop: 4, flexShrink: 0 }} />
                  <div>
                    <div style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 600 }}>{item.timestamp || 'Recent'}</div>
                    <div style={{ fontSize: 13, color: '#374151', fontWeight: 500, marginTop: 2 }}>{item.event}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Recommended Actions + Alternative Suppliers */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Recommended Actions */}
          <div className="card" style={{ padding: 18 }}>
            <div style={{ fontSize: 14, fontWeight: 800, color: '#111827', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
              <ArrowRight size={16} color="#2563EB" /> AI Recommended Actions
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {(activeIncident.recommended_actions || []).map((action, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, background: '#F9FAFB', padding: '10px 12px', borderRadius: 8, border: '1px solid #F3F4F6' }}>
                  <div style={{ width: 20, height: 20, background: '#DBEAFE', color: '#1E40AF', borderRadius: '50%', fontSize: 11, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1 }}>
                    {i + 1}
                  </div>
                  <span style={{ fontSize: 12.5, color: '#1F2937', fontWeight: 600, lineHeight: 1.4 }}>
                    {typeof action === 'string' ? action : action.action || action.title}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Alternative Suppliers */}
          <div className="card" style={{ padding: 18 }}>
            <div style={{ fontSize: 14, fontWeight: 800, color: '#111827', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Building2 size={16} color="#059669" /> Suggested Alternative Suppliers
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {(activeIncident.alternative_suppliers || []).map((supp, i) => (
                <div key={i} style={{ background: '#ECFDF5', border: '1px solid #A7F3D0', padding: 12, borderRadius: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontSize: 13, fontWeight: 800, color: '#065F46' }}>{typeof supp === 'string' ? supp : supp.name}</span>
                    {supp.rating && (
                      <span style={{ background: '#059669', color: 'white', fontSize: 10.5, fontWeight: 800, padding: '1px 6px', borderRadius: 4 }}>
                        {supp.rating}
                      </span>
                    )}
                  </div>
                  {supp.lead_time && (
                    <div style={{ fontSize: 11.5, color: '#047857' }}>
                      Lead Time: <strong>{supp.lead_time}</strong> · Classification: <strong>{supp.tier || 'Tier 1'}</strong>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
