import { useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, Play, CheckCircle, XCircle, RotateCw, Clock, ChevronRight } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useAppStore } from '../store/appStore';

const agentEmoji = {
  'news_agent':           '📰',
  'risk_agent':           '⚠️',
  'graph_agent':          '🔗',
  'supplier_agent':       '🏭',
  'inventory_agent':      '📦',
  'recommendation_agent': '🎯',
};

function agentStatusColor(status) {
  if (status === 'completed') return { bg: '#D1FAE5', text: '#065F46', dot: '#059669' };
  if (status === 'running')   return { bg: '#EFF6FF', text: '#1E40AF', dot: '#2563EB' };
  if (status === 'failed')    return { bg: '#FEE2E2', text: '#991B1B', dot: '#DC2626' };
  if (status === 'retrying')  return { bg: '#FEF3C7', text: '#92400E', dot: '#D97706' };
  return { bg: '#F3F4F6', text: '#374151', dot: '#9CA3AF' };
}

function AgentCard({ agent, delay }) {
  const sc = agentStatusColor(agent.status);
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
      className="card" style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ fontSize: 22 }}>{agentEmoji[agent.agent_id] || '🤖'}</div>
          <div>
            <div style={{ fontSize: 12.5, fontWeight: 700, color: '#111827' }}>{agent.agent_id}</div>
            <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 1 }}>{agent.agent_type || 'AI Agent'}</div>
          </div>
        </div>
        <span style={{ background: sc.bg, color: sc.text, fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 10, textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 3, flexShrink: 0 }}>
          <span style={{ width: 5, height: 5, borderRadius: '50%', background: sc.dot, display: 'inline-block' }} />
          {agent.status || 'idle'}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {[
          { label: 'Version',      value: agent.version || '—' },
          { label: 'Enabled',      value: agent.enabled ? 'Yes' : 'No' },
          { label: 'Total Runs',   value: agent.total_executions ?? '—' },
          { label: 'Success Rate', value: agent.success_rate != null ? `${(agent.success_rate * 100).toFixed(0)}%` : '—' },
        ].map(row => (
          <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#6B7280', padding: '2px 0' }}>
            <span>{row.label}</span>
            <span style={{ fontWeight: 600, color: '#374151' }}>{row.value}</span>
          </div>
        ))}
      </div>

      {agent.last_execution_at && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: '#9CA3AF' }}>
          <Clock size={11} /> Last run: {new Date(agent.last_execution_at).toLocaleTimeString()}
        </div>
      )}
    </motion.div>
  );
}

export default function Orchestration() {
  const [running, setRunning] = useState(false);
  const { setActiveWorkflow } = useAppStore();
  const qc = useQueryClient();

  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ['orchestrator-status'],
    queryFn:  () => api.get('/orchestrator/status'),
    refetchInterval: running ? 3000 : 30000,
  });

  const { data: events, refetch: refetchEvents } = useQuery({
    queryKey: ['orchestrator-events'],
    queryFn:  () => api.get('/orchestrator/events?limit=40'),
    refetchInterval: running ? 2000 : 60000,
  });

  const { data: runs } = useQuery({
    queryKey: ['orchestrator-runs'],
    queryFn:  () => api.get('/orchestrator/runs?limit=5'),
  });

  const triggerMutation = useMutation({
    mutationFn: () => api.post('/orchestrator/trigger', { trigger_type: 'manual', payload: {} }),
    onMutate: () => { setRunning(true); setActiveWorkflow(true); },
    onSuccess: () => {
      setRunning(false);
      setActiveWorkflow(false);
      qc.invalidateQueries({ queryKey: ['orchestrator-status'] });
      qc.invalidateQueries({ queryKey: ['orchestrator-events'] });
      qc.invalidateQueries({ queryKey: ['orchestrator-runs'] });
    },
    onError: () => { setRunning(false); setActiveWorkflow(false); },
  });

  const agents = status?.agents || [];
  const eventList = Array.isArray(events?.events) ? events.events : [];
  const runList   = Array.isArray(runs?.runs)     ? runs.runs     : [];

  // Workflow pipeline order
  const pipelineOrder = status?.workflow_plan || agents.map(a => a.agent_id);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1300 }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827' }}>AI Orchestration Center</h1>
            {running && (
              <span style={{ background: '#EFF6FF', color: '#2563EB', fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 6, height: 6, background: '#2563EB', borderRadius: '50%', animation: 'agent-pulse 1.5s ease-in-out infinite' }} /> LIVE
              </span>
            )}
          </div>
          <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Visualize and control the multi-agent AI workflow for supply chain intelligence</p>
        </div>
        <button onClick={() => triggerMutation.mutate()} disabled={running}
          style={{ display: 'flex', alignItems: 'center', gap: 8, background: running ? '#F3F4F6' : 'linear-gradient(135deg, #2563EB, #7C3AED)', color: running ? '#9CA3AF' : 'white', border: 'none', borderRadius: 10, padding: '10px 20px', fontSize: 13, fontWeight: 600, cursor: running ? 'not-allowed' : 'pointer', boxShadow: running ? 'none' : '0 4px 14px rgba(37,99,235,0.35)', transition: 'all 0.2s' }}>
          {running ? <><RotateCw size={15} /> Running Workflow...</> : <><Play size={15} /> Run AI Workflow</>}
        </button>
      </motion.div>

      {/* Workflow Pipeline */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        className="card" style={{ padding: 20, background: 'linear-gradient(135deg, #FAFBFF 0%, #F0F4FF 100%)' }}
      >
        <div style={{ fontSize: 12, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 14 }}>Workflow Pipeline</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 0, overflowX: 'auto', paddingBottom: 4 }}>
          {(agents.length > 0 ? agents : pipelineOrder.map(id => ({ agent_id: id, status: 'idle' }))).map((agent, i) => {
            const sc = agentStatusColor(agent.status);
            return (
              <div key={agent.agent_id || i} style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, minWidth: 90 }}>
                  <div style={{ width: 44, height: 44, background: sc.bg, border: `2px solid ${sc.dot}`, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, position: 'relative' }}>
                    {agentEmoji[agent.agent_id] || '🤖'}
                    {agent.status === 'completed' && (
                      <div style={{ position: 'absolute', bottom: -4, right: -4, background: '#059669', borderRadius: '50%', width: 14, height: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid white' }}>
                        <CheckCircle size={8} color="white" strokeWidth={3} />
                      </div>
                    )}
                  </div>
                  <div style={{ fontSize: 10, fontWeight: 600, color: sc.text, textAlign: 'center', lineHeight: 1.2, maxWidth: 80 }}>{(agent.agent_id || '').replace('_agent', '')}</div>
                </div>
                {i < agents.length - 1 && (
                  <div style={{ display: 'flex', alignItems: 'center', width: 30, flexShrink: 0, position: 'relative', top: -10 }}>
                    <div style={{ height: 2, flex: 1, background: agent.status === 'completed' ? '#059669' : '#E5E7EB', transition: 'background 0.5s' }} />
                    <ChevronRight size={12} color={agent.status === 'completed' ? '#059669' : '#D1D5DB'} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* Agents Grid + Event Log */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 16, alignItems: 'start' }}>
        {/* Agent cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
          {agents.length > 0
            ? agents.map((agent, i) => <AgentCard key={agent.agent_id || i} agent={agent} delay={i * 0.06} />)
            : Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="card" style={{ padding: 16, height: 140, background: '#FAFAFA', animation: 'pulse 1.5s infinite' }} />
              ))}
        </div>

        {/* Event Bus Log */}
        <motion.div initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }} className="card" style={{ overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #F3F4F6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', display: 'flex', alignItems: 'center', gap: 6 }}>
              <Activity size={14} color="#2563EB" /> Event Log
            </div>
            {running && (
              <span style={{ fontSize: 11, color: '#059669', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 6, height: 6, background: '#059669', borderRadius: '50%' }} /> Live
              </span>
            )}
          </div>
          <div className="terminal" style={{ height: 380, borderRadius: 0 }}>
            {eventList.length === 0 && !running && (
              <div style={{ color: '#6B7280', fontStyle: 'italic', padding: 8 }}>No events yet. Click "Run AI Workflow" to start.</div>
            )}
            {eventList.map((ev, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}
                style={{ marginBottom: 3 }}
              >
                <span className="log-muted">{ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '—'} </span>
                <span className={ev.event_type?.includes('FAILED') ? 'log-warn' : ev.event_type?.includes('COMPLETED') ? 'log-success' : 'log-info'}>
                  [{ev.agent_id || ev.source || 'orchestrator'}] {ev.event_type || ''}{ev.message ? `: ${ev.message}` : ''}
                </span>
              </motion.div>
            ))}
            {running && <div style={{ color: '#6B7280', fontStyle: 'italic' }} className="cursor-blink">Processing...</div>}
          </div>
        </motion.div>
      </div>

      {/* Recent Runs */}
      {runList.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 14 }}>Recent Workflow Runs</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {runList.map(run => (
              <div key={run.execution_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#FAFAFA', borderRadius: 8 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  {run.status === 'completed' ? <CheckCircle size={14} color="#059669" /> : run.status === 'failed' ? <XCircle size={14} color="#DC2626" /> : <RotateCw size={14} color="#2563EB" />}
                  <span style={{ fontSize: 12, fontWeight: 500, color: '#374151' }}>{run.execution_id.slice(0, 8)}…</span>
                  <span style={{ fontSize: 11, color: '#9CA3AF' }}>{run.trigger_type}</span>
                </div>
                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                  <span style={{ fontSize: 11, color: '#9CA3AF' }}>{run.started_at ? new Date(run.started_at).toLocaleString() : '—'}</span>
                  <span style={{ background: run.status === 'completed' ? '#D1FAE5' : run.status === 'failed' ? '#FEE2E2' : '#EFF6FF', color: run.status === 'completed' ? '#065F46' : run.status === 'failed' ? '#991B1B' : '#1E40AF', fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 8, textTransform: 'uppercase' }}>{run.status}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
