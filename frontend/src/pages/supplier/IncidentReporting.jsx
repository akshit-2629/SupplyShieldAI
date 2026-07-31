import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Plus, CheckCircle2, Clock, FileText, X, ChevronDown } from 'lucide-react';
import PageHeader from '../../components/supplier/shared/PageHeader';
import StatusBadge from '../../components/supplier/shared/StatusBadge';
import EmptyState from '../../components/supplier/shared/EmptyState';
import FileUploadZone from '../../components/supplier/shared/FileUploadZone';
import { createIncident, getIncidents, uploadIncidentAttachment } from '../../services/supplierApi';

const CATEGORIES = [
  { id: 'machine_failure', label: 'Machine Failure', icon: '⚙️' },
  { id: 'natural_disaster', label: 'Natural Disaster', icon: '🌪️' },
  { id: 'power_failure', label: 'Power Failure', icon: '⚡' },
  { id: 'flood', label: 'Flood', icon: '🌊' },
  { id: 'earthquake', label: 'Earthquake', icon: '🌍' },
  { id: 'labor_strike', label: 'Labor Strike', icon: '✊' },
  { id: 'raw_material_shortage', label: 'Raw Material Shortage', icon: '📦' },
  { id: 'transportation_delay', label: 'Transportation Delay', icon: '🚚' },
  { id: 'cyber_incident', label: 'Cyber Incident', icon: '🔐' },
  { id: 'quality_issue', label: 'Quality Issue', icon: '⚠️' },
];

const SEVERITIES = [
  { id: 'low', label: 'Low', color: '#10B981', bg: '#ECFDF5', desc: 'Minor disruption, business continues normally' },
  { id: 'medium', label: 'Medium', color: '#F59E0B', bg: '#FFFBEB', desc: 'Moderate impact, some operations affected' },
  { id: 'high', label: 'High', color: '#EF4444', bg: '#FEF2F2', desc: 'Significant disruption, major operations halted' },
  { id: 'critical', label: 'Critical', color: '#7F1D1D', bg: '#FEE2E2', desc: 'Complete shutdown or irreversible damage' },
];

function IncidentCard({ incident }) {
  const [expanded, setExpanded] = useState(false);
  const cat = CATEGORIES.find((c) => c.id === incident.category);
  const sev = SEVERITIES.find((s) => s.id === incident.severity);
  return (
    <div className="card" style={{ padding: '16px 20px', cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: sev?.bg || '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>
          {cat?.icon || '⚠️'}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 2 }}>{cat?.label || incident.category}</div>
          <div style={{ fontSize: 12, color: '#9CA3AF' }}>{new Date(incident.createdAt || Date.now()).toLocaleDateString()}</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <StatusBadge status={incident.severity} />
          <StatusBadge status={incident.status || 'pending'} />
          <ChevronDown size={15} color="#9CA3AF" style={{ transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
        </div>
      </div>
      <AnimatePresence>
        {expanded && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            style={{ overflow: 'hidden', marginTop: 14, paddingTop: 14, borderTop: '1px solid #F3F4F6' }}>
            <p style={{ fontSize: 13.5, color: '#374151', lineHeight: 1.6 }}>{incident.description || 'No description provided.'}</p>
            {incident.expectedRecovery && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10, fontSize: 13, color: '#6B7280' }}>
                <Clock size={13} /> Expected recovery: {incident.expectedRecovery}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function IncidentReporting() {
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  const [form, setForm] = useState({
    category: '',
    severity: '',
    title: '',
    description: '',
    expectedRecovery: '',
    affectedAreas: '',
    currentStatus: '',
    files: [],
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getIncidents();
      const items = Array.isArray(res) ? res : (res?.items || []);
      setIncidents(items.map(i => ({
        id: i.id,
        category: (i.incident_type || '').toLowerCase(),
        severity: (i.severity || 'medium').toLowerCase(),
        status: (i.status || 'ACTIVE').toLowerCase(),
        title: i.title,
        description: i.description,
        expectedRecovery: i.estimated_recovery_days ? `${i.estimated_recovery_days} days` : null,
        createdAt: i.reported_at || i.created_at
      })));
    } catch (err) {
      console.error('Failed to load incidents:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const set = (k) => (v) => {
    setValidationError('');
    setForm((p) => ({ ...p, [k]: typeof v === 'object' && v.target ? v.target.value : v }));
  };

  async function handleSubmit(e) {
    e.preventDefault();
    console.log("[INCIDENT] SUBMIT HANDLER FIRED");
    console.log("[INCIDENT] FORM DATA:", form);

    if (!form.category) {
      setValidationError("Incident category is required.");
      return;
    }
    if (!form.severity) {
      setValidationError("Incident severity is required.");
      return;
    }
    if (!form.title?.trim()) {
      setValidationError("Incident title is required.");
      return;
    }
    if (form.title.trim().length < 5) {
      setValidationError("Incident title must be at least 5 characters long.");
      return;
    }
    if (!form.description?.trim()) {
      setValidationError("Incident description is required.");
      return;
    }
    if (form.description.trim().length < 10) {
      setValidationError("Incident description must be at least 10 characters long.");
      return;
    }

    setValidationError('');
    console.log("[INCIDENT] ABOUT TO CALL API");
    setSubmitting(true);

    try {
      const catMap = {
        machine_failure: 'MACHINE_FAILURE',
        natural_disaster: 'OTHER',
        power_failure: 'POWER_FAILURE',
        flood: 'FLOOD',
        earthquake: 'EARTHQUAKE',
        labor_strike: 'STRIKE',
        raw_material_shortage: 'MATERIAL_SHORTAGE',
        transportation_delay: 'TRANSPORTATION_DELAY',
        cyber_incident: 'CYBER_ATTACK',
        quality_issue: 'QUALITY_ISSUE',
      };
      const catObj = CATEGORIES.find(c => c.id === form.category);
      const catLabel = catObj ? catObj.label : form.category;
      const desc = form.description.trim();

      let recDays = null;
      if (form.expectedRecovery) {
        if (/^\d+$/.test(form.expectedRecovery)) {
          recDays = parseInt(form.expectedRecovery, 10);
        } else {
          const recDate = new Date(form.expectedRecovery);
          if (!isNaN(recDate.getTime())) {
            const diffMs = recDate.getTime() - Date.now();
            recDays = Math.max(1, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
          }
        }
      }

      const payload = {
        incident_type: catMap[form.category] || 'OTHER',
        severity: (form.severity || 'medium').toUpperCase(),
        title: form.title.trim(),
        description: desc,
        estimated_recovery_days: recDays,
      };

      const created = await createIncident(payload);

      if (created?.id && form.files && form.files.length > 0) {
        for (const file of form.files) {
          try {
            await uploadIncidentAttachment(created.id, file);
          } catch (attErr) {
            console.error('[INCIDENT] Attachment upload error:', attErr);
          }
        }
      }

      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        setShowForm(false);
        setForm({ category: '', severity: '', title: '', description: '', expectedRecovery: '', affectedAreas: '', currentStatus: '', files: [] });
        load();
      }, 2000);
    } catch (err) {
      console.error('[INCIDENT] Submit incident error:', err);
      setValidationError(err.message || 'Failed to submit incident report');
    } finally {
      setSubmitting(false);
    }
  }

  const inputSt = { width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '9px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box' };
  const labelSt = { fontSize: 11, fontWeight: 700, color: '#6B7280', display: 'block', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' };

  return (
    <div>
      <PageHeader
        title="Incident Reporting"
        description="Report supply chain disruptions, operational incidents, and production issues"
        actions={
          <button onClick={() => setShowForm(!showForm)}
            style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '9px 18px', border: 'none', borderRadius: 9, fontSize: 13.5, fontWeight: 700, background: showForm ? '#F3F4F6' : 'linear-gradient(135deg, #EF4444, #DC2626)', color: showForm ? '#374151' : 'white', cursor: 'pointer', boxShadow: showForm ? 'none' : '0 2px 10px rgba(239,68,68,0.3)' }}>
            {showForm ? <><X size={15} /> Cancel</> : <><Plus size={15} /> Report Incident</>}
          </button>
        }
      />

      {/* Incident form */}
      <AnimatePresence>
        {showForm && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} style={{ overflow: 'hidden', marginBottom: 24 }}>
            <div className="card" style={{ padding: '24px 28px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
                <div style={{ width: 36, height: 36, borderRadius: 10, background: '#FEF2F2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><AlertTriangle size={18} color="#EF4444" /></div>
                <div>
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>Report New Incident</h3>
                  <p style={{ fontSize: 12, color: '#6B7280' }}>All incidents are reviewed by the SupplyShield AI team</p>
                </div>
              </div>

              {submitted ? (
                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} style={{ textAlign: 'center', padding: '32px 0' }}>
                  <div style={{ width: 60, height: 60, background: '#ECFDF5', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                    <CheckCircle2 size={30} color="#10B981" />
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: '#111827', marginBottom: 6 }}>Incident Reported Successfully</h3>
                  <p style={{ fontSize: 13, color: '#6B7280' }}>Our AI system will process and prioritize this incident.</p>
                </motion.div>
              ) : (
                <form onSubmit={handleSubmit}>
                  {validationError && (
                    <div style={{ padding: '10px 14px', borderRadius: 8, background: '#FEF2F2', border: '1px solid #FCA5A5', color: '#991B1B', fontSize: 13, fontWeight: 600, marginBottom: 18, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <AlertTriangle size={16} color="#DC2626" />
                      <span>{validationError}</span>
                    </div>
                  )}

                  {/* Category */}
                  <div style={{ marginBottom: 20 }}>
                    <label style={labelSt}>Incident Category *</label>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: 10 }}>
                      {CATEGORIES.map((cat) => (
                        <button key={cat.id} type="button" onClick={() => set('category')(cat.id)}
                          style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', border: `1.5px solid ${form.category === cat.id ? '#EF4444' : '#E5E7EB'}`, borderRadius: 9, background: form.category === cat.id ? '#FEF2F2' : 'white', cursor: 'pointer', transition: 'all 0.15s', textAlign: 'left' }}>
                          <span style={{ fontSize: 18 }}>{cat.icon}</span>
                          <span style={{ fontSize: 12.5, fontWeight: form.category === cat.id ? 700 : 500, color: form.category === cat.id ? '#DC2626' : '#374151' }}>{cat.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Severity */}
                  <div style={{ marginBottom: 20 }}>
                    <label style={labelSt}>Severity Level *</label>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
                      {SEVERITIES.map((sev) => (
                        <button key={sev.id} type="button" onClick={() => set('severity')(sev.id)}
                          style={{ padding: '10px 12px', border: `1.5px solid ${form.severity === sev.id ? sev.color : '#E5E7EB'}`, borderRadius: 9, background: form.severity === sev.id ? sev.bg : 'white', cursor: 'pointer', textAlign: 'center', transition: 'all 0.15s' }}>
                          <div style={{ fontSize: 13.5, fontWeight: 700, color: sev.color }}>{sev.label}</div>
                          <div style={{ fontSize: 10.5, color: '#9CA3AF', marginTop: 2, lineHeight: 1.3 }}>{sev.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                    <div style={{ gridColumn: 'span 2' }}>
                      <label style={labelSt}>Incident Title *</label>
                      <input style={inputSt} value={form.title} onChange={set('title')} placeholder="Brief title describing the incident" onFocus={(e) => e.target.style.borderColor='#EF4444'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} />
                    </div>
                    <div style={{ gridColumn: 'span 2' }}>
                      <label style={labelSt}>Detailed Description *</label>
                      <textarea style={{ ...inputSt, resize: 'vertical' }} rows={4} value={form.description} onChange={set('description')} placeholder="Describe the incident in detail — what happened, when, and the immediate impact..." onFocus={(e) => e.target.style.borderColor='#EF4444'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} />
                    </div>
                    <div>
                      <label style={labelSt}>Affected Areas</label>
                      <input style={inputSt} value={form.affectedAreas} onChange={set('affectedAreas')} placeholder="Factory A, Warehouse B, Line 3…" onFocus={(e) => e.target.style.borderColor='#EF4444'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} />
                    </div>
                    <div>
                      <label style={labelSt}>Expected Recovery Date</label>
                      <input type="date" style={inputSt} value={form.expectedRecovery} onChange={set('expectedRecovery')} onFocus={(e) => e.target.style.borderColor='#EF4444'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} />
                    </div>
                    <div style={{ gridColumn: 'span 2' }}>
                      <label style={labelSt}>Current Mitigation Status</label>
                      <input style={inputSt} value={form.currentStatus} onChange={set('currentStatus')} placeholder="What steps are currently being taken?" onFocus={(e) => e.target.style.borderColor='#EF4444'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} />
                    </div>
                  </div>

                  <div style={{ marginBottom: 20 }}>
                    <label style={labelSt}>Attachments (Photos, Documents)</label>
                    <FileUploadZone onFiles={(f) => set('files')(Array.from(f))} accept={['image/*', '.pdf']} multiple hint="Drag & drop photos or documents, or click to browse" />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                    <button type="button" onClick={() => setShowForm(false)} style={{ padding: '10px 20px', border: '1px solid #E5E7EB', borderRadius: 9, fontSize: 13.5, background: 'white', color: '#374151', cursor: 'pointer', fontWeight: 600 }}>Cancel</button>
                    <button type="submit" disabled={submitting}
                      style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '10px 22px', border: 'none', borderRadius: 9, fontSize: 13.5, fontWeight: 700, background: submitting ? '#9CA3AF' : 'linear-gradient(135deg, #EF4444, #DC2626)', color: 'white', cursor: submitting ? 'not-allowed' : 'pointer' }}>
                      <AlertTriangle size={15} />{submitting ? 'Submitting…' : 'Submit Incident Report'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Incidents list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {incidents.length === 0 ? (
          <div className="card" style={{ padding: 0 }}>
            <EmptyState type="file" title="No incidents reported" description="Your supply chain is running smoothly. Use the button above to report any disruptions." actionLabel="Report Incident" onAction={() => setShowForm(true)} />
          </div>
        ) : (
          incidents.map((inc, i) => <IncidentCard key={i} incident={inc} />)
        )}
      </div>
    </div>
  );
}
