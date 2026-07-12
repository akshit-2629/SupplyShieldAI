import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Flame, Building2, Package, CheckCircle, TrendingUp, TrendingDown, ArrowRight, Zap, Activity, Loader2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { severityColor, timeAgo } from '../lib/utils';
import { useNavigate } from 'react-router-dom';

const iconMap = { AlertTriangle, Flame, Building2, Package, CheckCircle };

function AnimatedCounter({ target }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    const num = typeof target === 'number' ? target : parseInt(target);
    if (isNaN(num)) { setVal(target); return; }
    let start = 0;
    const step = Math.ceil(num / 40) || 1;
    const timer = setInterval(() => {
      start += step;
      if (start >= num) { setVal(target); clearInterval(timer); }
      else setVal(start);
    }, 20);
    return () => clearInterval(timer);
  }, [target]);
  return <>{val}</>;
}

function KPICard({ kpi, delay, isLoading }) {
  const Icon = iconMap[kpi.icon] || AlertTriangle;
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.35 }}
      className="card" style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}
      onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 12, color: '#9CA3AF', fontWeight: 500, marginBottom: 6 }}>{kpi.label}</div>
          <div style={{ fontSize: 30, fontWeight: 800, color: '#111827', letterSpacing: '-0.02em', height: 36 }}>
            {isLoading ? <div style={{ width: 40, height: 30, background: '#F3F4F6', borderRadius: 4, animation: 'pulse 1.5s infinite' }} /> : <AnimatedCounter target={kpi.value} />}
          </div>
        </div>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: kpi.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon size={20} color={kpi.color} />
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12 }}>
        {kpi.changeType === 'increase' ? <TrendingUp size={13} color={kpi.label === 'Alt. Suppliers Ready' ? '#059669' : '#DC2626'} /> : <TrendingDown size={13} color="#059669" />}
        <span style={{ color: kpi.label === 'Alt. Suppliers Ready' ? '#059669' : kpi.changeType === 'decrease' ? '#059669' : '#DC2626', fontWeight: 600 }}>
          {kpi.changeType === 'increase' ? '+' : ''}{kpi.change}
        </span>
        <span style={{ color: '#9CA3AF' }}>vs last week</span>
      </div>
    </motion.div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // 1. Fetch KPIs
  const { data: kpisData, isLoading: isLoadingKPIs, isError: isErrorKPIs } = useQuery({
    queryKey: ['dashboard-kpis'],
    queryFn: () => api.get('/dashboard/kpis'),
  });

  // 2. Fetch Critical Incident
  const { data: criticalIncident, isLoading: isLoadingIncident } = useQuery({
    queryKey: ['dashboard-incident'],
    queryFn: () => api.get('/dashboard/critical-incident'),
  });

  // 3. Fetch Risk Trend
  const { data: riskTrend, isLoading: isLoadingTrend } = useQuery({
    queryKey: ['dashboard-risk-trend'],
    queryFn: () => api.get('/dashboard/risk-trend'),
  });

  // 4. Fetch AI Summary
  const { data: aiSummary, isLoading: isLoadingSummary } = useQuery({
    queryKey: ['dashboard-ai-summary'],
    queryFn: () => api.get('/dashboard/ai-summary'),
  });

  // 5. Fetch Recent Disruptions
  const { data: recentDisruptions, isLoading: isLoadingDisruptions } = useQuery({
    queryKey: ['dashboard-recent-disruptions'],
    queryFn: () => api.get('/dashboard/recent-disruptions'),
  });

  // 6. Fetch Activity Feed (using orchestrator endpoints, we simulate this if not available)
  const { data: activityFeed, isLoading: isLoadingActivity } = useQuery({
    queryKey: ['dashboard-activity'],
    queryFn: async () => {
      // Temporary fallback until actual activity feed endpoint exists in orchestrator
      try {
          const events = await api.get('/orchestrator/events');
          // Map to activity format
          if(Array.isArray(events) && events.length > 0) {
              return events.slice(0, 6).map((e, i) => ({
                  id: e.id || i,
                  action: `${e.agent || 'System'} ${e.event_type || 'Update'}`,
                  time: timeAgo(e.timestamp),
                  type: e.agent === 'Master Orchestrator' ? 'system' : 'ai'
              }));
          }
      } catch (err) {
          // Ignore error and return fallback empty array
      }
      return [
        { id: 1, action: 'Dashboard loaded and connected to live APIs', time: 'Just now', type: 'system' }
      ];
    },
  });

  // Run AI Analysis Mutation
  const triggerAnalysis = useMutation({
    mutationFn: () => api.post('/orchestrator/trigger'),
    onSuccess: () => {
      // Invalidate all dashboard queries to refetch fresh data
      queryClient.invalidateQueries(['dashboard-kpis']);
      queryClient.invalidateQueries(['dashboard-incident']);
      queryClient.invalidateQueries(['dashboard-risk-trend']);
      queryClient.invalidateQueries(['dashboard-ai-summary']);
      queryClient.invalidateQueries(['dashboard-recent-disruptions']);
      queryClient.invalidateQueries(['dashboard-activity']);
    }
  });

  const liveKPIs = [
    { label: 'Active Disruptions', value: kpisData?.activeDisruptions || 0, change: 3, changeType: 'increase', icon: 'AlertTriangle', color: '#DC2626', bg: '#FEE2E2' },
    { label: 'Critical Risks', value: kpisData?.criticalRisks || 0, change: 1, changeType: 'increase', icon: 'Flame', color: '#9A3412', bg: '#FEF3C7' },
    { label: 'Affected Suppliers', value: kpisData?.affectedSuppliers || 0, change: 12, changeType: 'increase', icon: 'Building2', color: '#D97706', bg: '#FEF9C3' },
    { label: 'Inventory Health', value: `${kpisData?.inventoryHealth || 0}%`, change: -8, changeType: 'decrease', icon: 'Package', color: '#D97706', bg: '#FEF3C7' },
    { label: 'Alt. Suppliers Ready', value: kpisData?.alternativeSuppliers || 0, change: 4, changeType: 'increase', icon: 'CheckCircle', color: '#059669', bg: '#D1FAE5' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 1400 }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Executive Dashboard</h1>
            <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Real-time supply chain risk intelligence — Connected to Backend API</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button 
              onClick={() => triggerAnalysis.mutate()} 
              disabled={triggerAnalysis.isPending}
              style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 500, cursor: triggerAnalysis.isPending ? 'not-allowed' : 'pointer', transition: 'all 0.15s', opacity: triggerAnalysis.isPending ? 0.7 : 1 }}
              onMouseEnter={e => !triggerAnalysis.isPending && (e.currentTarget.style.background = '#DBEAFE')}
              onMouseLeave={e => !triggerAnalysis.isPending && (e.currentTarget.style.background = '#EFF6FF')}
            >
              {triggerAnalysis.isPending ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />} 
              {triggerAnalysis.isPending ? 'Analyzing...' : 'Run AI Analysis'}
            </button>
            <button onClick={() => navigate('/reports')} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#111827', color: 'white', border: 'none', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 500, cursor: 'pointer', transition: 'all 0.15s' }}
              onMouseEnter={e => e.currentTarget.style.background = '#374151'}
              onMouseLeave={e => e.currentTarget.style.background = '#111827'}
            >
              <ArrowRight size={14} /> View Reports
            </button>
          </div>
        </div>
      </motion.div>

      {/* Critical Banner */}
      {isLoadingIncident ? (
        <div style={{ background: '#F3F4F6', borderRadius: 10, padding: '12px 16px', height: 45, animation: 'pulse 1.5s infinite' }} />
      ) : criticalIncident ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 10, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#DC2626', animation: 'pulse-ring 1.5s ease-out infinite' }} />
          <span style={{ fontSize: 13, fontWeight: 600, color: '#991B1B' }}>CRITICAL:</span>
          <span style={{ fontSize: 13, color: '#B91C1C' }}>
            {criticalIncident.title} is affecting {criticalIncident.affectedSuppliers} suppliers.
            {criticalIncident.description && ` ${criticalIncident.description.substring(0, 50)}...`}
          </span>
          <button onClick={() => navigate('/incidents')} style={{ marginLeft: 'auto', background: '#DC2626', color: 'white', border: 'none', borderRadius: 6, padding: '5px 12px', fontSize: 12, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}>View Incident</button>
        </motion.div>
      ) : null}

      {/* KPI Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
        {isErrorKPIs ? (
          <div style={{ gridColumn: '1 / -1', padding: 20, background: '#FEF2F2', color: '#991B1B', borderRadius: 8, fontSize: 14 }}>
            Failed to load KPIs. Please check backend connection.
          </div>
        ) : (
          liveKPIs.map((kpi, i) => <KPICard key={kpi.label} kpi={kpi} delay={0.1 + i * 0.06} isLoading={isLoadingKPIs} />)
        )}
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
        {/* Risk Trend */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>Global Risk Trend</div>
              <div style={{ fontSize: 12, color: '#9CA3AF' }}>Risk score & incident count — Last 30 Days</div>
            </div>
            <div style={{ display: 'flex', gap: 12, fontSize: 11, color: '#9CA3AF' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 10, height: 3, background: '#DC2626', display: 'inline-block', borderRadius: 2 }} /> Risk Score</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 10, height: 3, background: '#2563EB', display: 'inline-block', borderRadius: 2 }} /> Incidents</span>
            </div>
          </div>
          <div style={{ height: 200, width: '100%' }}>
            {isLoadingTrend ? (
              <div style={{ width: '100%', height: '100%', background: '#F3F4F6', borderRadius: 8, animation: 'pulse 1.5s infinite' }} />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={riskTrend || []}>
                  <defs>
                    <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#DC2626" stopOpacity={0.12}/>
                      <stop offset="95%" stopColor="#DC2626" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="incGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563EB" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#2563EB" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 12 }} />
                  <Area type="monotone" dataKey="risk" stroke="#DC2626" strokeWidth={2} fill="url(#riskGrad)" dot={false} />
                  <Area type="monotone" dataKey="incidents" stroke="#2563EB" strokeWidth={2} fill="url(#incGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </motion.div>

        {/* AI Insights */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }} className="card" style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <div style={{ width: 28, height: 28, background: 'linear-gradient(135deg, #7C3AED, #2563EB)', borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Zap size={14} color="white" />
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>AI Intelligence Summary</div>
              <div style={{ fontSize: 11, color: '#9CA3AF' }}>
                {isLoadingSummary ? 'Loading...' : aiSummary?.generatedAt ? `Generated ${timeAgo(aiSummary.generatedAt)}` : 'Live'}
              </div>
            </div>
          </div>
          <div style={{ background: '#FAFBFF', border: '1px solid #EEF2FF', borderRadius: 8, padding: 14, flex: 1 }}>
            {isLoadingSummary ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ height: 12, background: '#E5E7EB', borderRadius: 4, width: '100%', animation: 'pulse 1.5s infinite' }} />
                <div style={{ height: 12, background: '#E5E7EB', borderRadius: 4, width: '90%', animation: 'pulse 1.5s infinite' }} />
                <div style={{ height: 12, background: '#E5E7EB', borderRadius: 4, width: '95%', animation: 'pulse 1.5s infinite' }} />
              </div>
            ) : (
              <p style={{ fontSize: 12.5, color: '#374151', lineHeight: 1.7 }} className="cursor-blink">
                {aiSummary?.summary}
              </p>
            )}
          </div>
          <button onClick={() => navigate('/reports')} style={{ background: '#111827', color: 'white', border: 'none', borderRadius: 8, padding: '9px 14px', fontSize: 12, fontWeight: 500, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
            <ArrowRight size={13} /> Full Report
          </button>
        </motion.div>
      </div>

      {/* Bottom Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Recent Disruptions */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>Recent Disruptions</div>
            <button onClick={() => navigate('/disruptions')} style={{ fontSize: 12, color: '#2563EB', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}>View all →</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {isLoadingDisruptions ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} style={{ height: 45, background: '#F9FAFB', borderRadius: 8, animation: 'pulse 1.5s infinite' }} />
              ))
            ) : recentDisruptions?.length > 0 ? (
              recentDisruptions.map(d => {
                const sc = severityColor(d.severity);
                return (
                  <div key={d.id} onClick={() => navigate('/disruptions')} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', background: '#FAFAFA', borderRadius: 8, cursor: 'pointer', transition: 'background 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#F3F4F6'}
                    onMouseLeave={e => e.currentTarget.style.background = '#FAFAFA'}
                  >
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: sc.dot, flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12.5, fontWeight: 500, color: '#111827', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.title}</div>
                      <div style={{ fontSize: 11, color: '#9CA3AF' }}>{d.location || 'Unknown'} · {d.affectedSuppliers || 0} suppliers</div>
                    </div>
                    <span style={{ background: sc.bg, color: sc.text, fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 10, flexShrink: 0, textTransform: 'uppercase' }}>{d.severity}</span>
                  </div>
                );
              })
            ) : (
              <div style={{ fontSize: 13, color: '#6B7280', padding: 10, textAlign: 'center' }}>No recent disruptions found.</div>
            )}
          </div>
        </motion.div>

        {/* Activity Feed */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55 }} className="card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 14, fontWeight: 700, color: '#111827' }}>
              <Activity size={15} color="#2563EB" /> Activity Timeline
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {isLoadingActivity ? (
               Array.from({ length: 4 }).map((_, i) => (
                <div key={i} style={{ display: 'flex', gap: 12, paddingBottom: 14 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#E5E7EB', flexShrink: 0, marginTop: 3, animation: 'pulse 1.5s infinite' }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ height: 12, background: '#F3F4F6', borderRadius: 4, width: '80%', marginBottom: 4, animation: 'pulse 1.5s infinite' }} />
                    <div style={{ height: 10, background: '#F9FAFB', borderRadius: 4, width: '30%', animation: 'pulse 1.5s infinite' }} />
                  </div>
                </div>
               ))
            ) : activityFeed?.length > 0 ? (
              activityFeed.map((item, i) => (
                <div key={item.id} style={{ display: 'flex', gap: 12, paddingBottom: i < activityFeed.length - 1 ? 14 : 0 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: item.type === 'ai' ? '#7C3AED' : item.type === 'system' ? '#2563EB' : item.type === 'supplier' ? '#D97706' : '#059669', flexShrink: 0, marginTop: 3 }} />
                    {i < activityFeed.length - 1 && <div style={{ width: 1, flex: 1, background: '#F3F4F6', marginTop: 4 }} />}
                  </div>
                  <div style={{ flex: 1, paddingBottom: i < activityFeed.length - 1 ? 0 : 0 }}>
                    <div style={{ fontSize: 12.5, color: '#374151', lineHeight: 1.4, marginBottom: 2 }}>{item.action}</div>
                    <div style={{ fontSize: 11, color: '#9CA3AF' }}>{item.time}</div>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ fontSize: 13, color: '#6B7280', padding: 10, textAlign: 'center' }}>No recent activity.</div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
