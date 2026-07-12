import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { MapPin, Clock, TrendingUp, Brain, FileText, ArrowRight, ExternalLink, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { severityColor, timeAgo } from '../lib/utils';

const typeColor = { critical: '#DC2626', action: '#2563EB', info: '#6B7280', ai: '#7C3AED' };

export default function Incidents() {
  const navigate = useNavigate();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['incidents-top'],
    queryFn:  () => api.get('/risk/assessments'),
  });

  const assessments = Array.isArray(data) ? data : Array.isArray(data?.assessments) ? data.assessments : [];
  const incident = assessments.find(a => a.risk_level === 'CRITICAL') || assessments[0] || null;

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1200 }}>
        <div style={{ height: 32, width: 300, background: '#F3F4F6', borderRadius: 6 }} />
        <div style={{ height: 120, background: '#F3F4F6', borderRadius: 10 }} />
        <div style={{ height: 400, background: '#F3F4F6', borderRadius: 10 }} />
      </div>
    );
  }

  if (!incident) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1200 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827' }}>Incident Investigation Center</h1>
        <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 10, padding: '24px 20px', textAlign: 'center', color: '#1E40AF' }}>
          <Brain size={36} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>No Incidents Found</div>
          <div style={{ fontSize: 13 }}>Run the AI Workflow to generate risk assessments first.</div>
          <button onClick={() => navigate('/orchestration')} style={{ marginTop: 12, background: '#2563EB', color: 'white', border: 'none', borderRadius: 8, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Go to Orchestration</button>
        </div>
      </div>
    );
  }

  const sc = severityColor((incident.risk_level || '').toLowerCase());

  // Build a timeline from what data we have
  const timeline = [
    { time: incident.assessed_at ? new Date(incident.assessed_at).toLocaleString() : '—', event: `Risk assessment created. Level: ${incident.risk_level}. Score: ${(incident.risk_score || 0).toFixed(0)}/100.`, type: 'critical' },
    { time: '—', event: `Countries involved: ${(incident.countries || []).join(', ') || 'Global'}.`, type: 'info' },
    { time: '—', event: `Industries affected: ${(incident.industries || []).join(', ') || 'Multiple sectors'}.`, type: 'info' },
    { time: '—', event: `Trajectory: ${incident.trajectory || 'Unknown'}. Confidence: ${incident.confidence_label || '—'}.`, type: 'ai' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1200 }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Incident Investigation Center</h1>
        <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Deep-dive analysis of high-impact supply chain disruptions</p>
      </motion.div>

      {/* Incident Header Card */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="card" style={{ padding: 20, borderLeft: `4px solid ${sc.dot}` }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <span style={{ background: sc.bg, color: sc.text, fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 10, textTransform: 'uppercase' }}>{incident.severity}</span>
              <span style={{ background: stc.bg, color: stc.text, fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 10, textTransform: 'capitalize', display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 5, height: 5, borderRadius: '50%', background: stc.text, display: 'inline-block' }} />{incident.status}
              </span>
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 800, color: '#111827', marginBottom: 6 }}>{incident.title}</h2>
            <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#9CA3AF', flexWrap: 'wrap' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><MapPin size={12} /> {incident.location}</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Clock size={12} /> {timeAgo(incident.timestamp)}</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Users size={12} /> {incident.affectedSuppliers} suppliers</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => navigate('/recommendations')} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
              <ArrowRight size={14} /> View Recommendations
            </button>
            <button onClick={() => navigate('/reports')} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#111827', color: 'white', border: 'none', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
              <FileText size={14} /> Full Report
            </button>
          </div>
        </div>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 16, alignItems: 'start' }}>
        {/* Left: Timeline + AI Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* AI Summary */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card" style={{ padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <div style={{ width: 28, height: 28, background: 'linear-gradient(135deg,#7C3AED,#2563EB)', borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Brain size={14} color="white" />
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>AI Situation Summary</div>
            </div>
            <p style={{ fontSize: 13, color: '#374151', lineHeight: 1.8 }}>
              <strong>{incident.title || 'Risk Event'}</strong> is classified as <strong>{incident.risk_level}</strong>
              with a risk score of <strong>{(incident.risk_score || 0).toFixed(0)}/100</strong>.
              Countries affected: <strong>{(incident.countries || []).join(', ') || 'Global'}</strong>.
              Industries: <strong>{(incident.industries || []).join(', ') || 'Multiple'}</strong>.<br/><br/>
              Trajectory: <strong>{incident.trajectory || 'Unknown'}</strong>. Confidence: <strong>{incident.confidence_label || '—'}</strong>.
              {incident.url && <><br/><br/>Source: <a href={incident.url} target="_blank" rel="noreferrer" style={{ color: '#2563EB' }}>{incident.source || 'View Article'}</a></>}
            </p>
          </motion.div>

          {/* Timeline */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="card" style={{ padding: 20 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 16 }}>Incident Timeline</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {timeline.map((item, i) => (
                <div key={i} style={{ display: 'flex', gap: 12, paddingBottom: i < timeline.length - 1 ? 14 : 0 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: typeColor[item.type], marginTop: 3 }} />
                    {i < timeline.length - 1 && <div style={{ width: 1, flex: 1, background: '#F3F4F6', marginTop: 3 }} />}
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: '#9CA3AF', marginBottom: 2 }}>{item.time}</div>
                    <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{item.event}</div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Right: Stats + Sources */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Metrics */}
          <motion.div initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }} className="card" style={{ padding: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', marginBottom: 12 }}>Impact Metrics</div>
            {[
              { label: 'Risk Score',   value: `${(incident.risk_score || 0).toFixed(0)}/100`,   color: '#DC2626' },
              { label: 'Risk Level',  value: incident.risk_level || '—',                          color: '#D97706' },
              { label: 'Confidence',  value: incident.confidence_label || '—',                    color: '#6B7280' },
              { label: 'Trajectory',  value: incident.trajectory || '—',                           color: '#D97706' },
              { label: 'Industries',  value: `${(incident.industries || []).length} sectors`,       color: '#6B7280' },
            ].map(m => (
              <div key={m.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #F3F4F6', fontSize: 13 }}>
                <span style={{ color: '#9CA3AF' }}>{m.label}</span>
                <span style={{ fontWeight: 700, color: m.color }}>{m.value}</span>
              </div>
            ))}
          </motion.div>

          {/* Source Articles */}
          <motion.div initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.35 }} className="card" style={{ padding: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', marginBottom: 12 }}>Source Articles</div>
            {incident.url ? (
              <a href={incident.url} target="_blank" rel="noreferrer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '8px 0', cursor: 'pointer', textDecoration: 'none' }}>
                <div>
                  <div style={{ fontSize: 12.5, fontWeight: 500, color: '#111827', marginBottom: 2 }}>{incident.title}</div>
                  <div style={{ fontSize: 11, color: '#9CA3AF' }}>{incident.source || 'Source'} · {incident.assessed_at ? new Date(incident.assessed_at).toLocaleDateString() : '—'}</div>
                </div>
                <ExternalLink size={13} color="#9CA3AF" style={{ flexShrink: 0, marginTop: 2 }} />
              </a>
            ) : (
              <div style={{ fontSize: 13, color: '#9CA3AF', padding: '8px 0' }}>No source URL available for this assessment.</div>
            )}
          </motion.div>

          {/* Recommendations chips */}
          <motion.div initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }} className="card" style={{ padding: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', marginBottom: 10 }}>Recommended Actions</div>
            {(incident.rule_engine_results || []).slice(0, 4).map((rule, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: '6px 0', borderBottom: i < 3 ? '1px solid #F9FAFB' : 'none' }}>
                <div style={{ width: 18, height: 18, background: '#D1FAE5', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1 }}>
                  <span style={{ fontSize: 9, fontWeight: 800, color: '#059669' }}>{i + 1}</span>
                </div>
                <span style={{ fontSize: 12.5, color: '#374151', lineHeight: 1.4 }}>{rule.rule_name || rule}: {rule.action || ''}</span>
              </div>
            ))}
            {(!incident.rule_engine_results || incident.rule_engine_results.length === 0) && (
              <div style={{ fontSize: 13, color: '#9CA3AF' }}>No rule engine actions triggered.</div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
