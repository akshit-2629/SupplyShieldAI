import { useCallback, useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ReactFlow,
  MiniMap, Controls, Background,
  addEdge, useNodesState, useEdgesState,
  Handle, Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
  Search, AlertTriangle, Package, Cpu, Building2, RefreshCw, X, Shield,
  Truck, FileText, CheckCircle2, Factory, Warehouse, Activity, Zap, Info
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

const colorMap = {
  COMPANY:          { bg: '#EFF6FF', border: '#3B82F6', text: '#1E40AF', icon: Building2 },
  FACTORY:          { bg: '#ECFDF5', border: '#10B981', text: '#065F46', icon: Factory },
  WAREHOUSE:        { bg: '#F5F3FF', border: '#8B5CF6', text: '#5B21B6', icon: Warehouse },
  PRODUCT:          { bg: '#FDF2F8', border: '#EC4899', text: '#9D174D', icon: Package },
  COMPONENT:        { bg: '#FEF3C7', border: '#F59E0B', text: '#92400E', icon: Cpu },
  PRODUCTION_LINE:  { bg: '#E0F2FE', border: '#0EA5E9', text: '#075985', icon: Activity },
  SUPPLIER:         { bg: '#DBEAFE', border: '#2563EB', text: '#1E3A8A', icon: Building2 },
  SHIPMENT:         { bg: '#F1F5F9', border: '#64748B', text: '#334155', icon: Truck },
  INCIDENT:         { bg: '#FEE2E2', border: '#EF4444', text: '#991B1B', icon: AlertTriangle },
  RECOMMENDATION:   { bg: '#DCFCE7', border: '#22C55E', text: '#14532D', icon: Zap },
  DOCUMENT:         { bg: '#F3F4F6', border: '#9CA3AF', text: '#374151', icon: FileText },
  QUALITY_ISSUE:    { bg: '#FFEDD5', border: '#F97316', text: '#9A3412', icon: AlertTriangle },
};

function CustomNode({ data }) {
  const c = colorMap[(data.type || '').toUpperCase()] || colorMap.COMPANY;
  const Icon = c.icon;
  return (
    <div style={{
      background: c.bg, border: `2px solid ${c.border}`, borderRadius: 10,
      padding: '10px 14px', minWidth: 160, boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      display: 'flex', alignItems: 'center', gap: 10, transition: 'box-shadow 0.2s', position: 'relative',
    }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.12)'}
      onMouseLeave={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)'}
    >
      <Handle type="target" position={Position.Top} style={{ background: c.border, border: 'none', width: 8, height: 8 }} />
      <Handle type="source" position={Position.Bottom} style={{ background: c.border, border: 'none', width: 8, height: 8 }} />

      <div style={{ width: 32, height: 32, background: c.border, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={16} color="white" />
      </div>
      <div>
        <div style={{ fontSize: 12.5, fontWeight: 700, color: c.text, marginBottom: 1 }}>{data.label}</div>
        <div style={{ fontSize: 10, color: c.text, opacity: 0.8, fontWeight: 600, textTransform: 'capitalize' }}>
          {(data.category || data.type || '').replace('_', ' ')}
        </div>
      </div>
      {(data.risk_score >= 70) && (
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#DC2626', position: 'absolute', top: 6, right: 6 }} />
      )}
    </div>
  );
}

const nodeTypes = { custom: CustomNode };

function transformSnapshot(rf) {
  const nodes = (rf?.nodes || []).map((n, i) => ({
    id:       String(n.id),
    type:     'custom',
    position: n.position || { x: (i % 5) * 220, y: Math.floor(i / 5) * 140 },
    data: {
      label:      n.data?.label  || n.id,
      type:       n.data?.node_type || n.type || 'COMPANY',
      category:   n.data?.category || n.type || 'Company',
      risk_score: n.data?.risk_score || 0,
      risk_level: n.data?.risk_level || 'LOW',
      details:    n.data?.details || {},
    },
  }));

  const edges = (rf?.edges || []).map((e, i) => ({
    id:     String(e.id || `e${i}`),
    source: String(e.source),
    target: String(e.target),
    label:  e.data?.label || e.label || '',
    animated: (e.data?.risk_level === 'HIGH' || e.data?.risk_level === 'CRITICAL'),
    style: { stroke: '#94A3B8', strokeWidth: 2 },
  }));

  return { nodes, edges };
}

export default function KnowledgeGraph() {
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedNode, setSelectedNode] = useState(null);

  const { data: snapshotData, isLoading, isError, refetch } = useQuery({
    queryKey: ['graph-snapshot'],
    queryFn: () => api.get('/graph/snapshot?max_nodes=150'),
    staleTime: 60_000,
    retry: 1,
  });

  const is_empty = snapshotData?.is_empty || !snapshotData?.react_flow?.nodes?.length;
  
  const { nodes: rawNodes, edges: rawEdges } = useMemo(() => {
    return !is_empty && snapshotData?.react_flow
      ? transformSnapshot(snapshotData.react_flow)
      : { nodes: [], edges: [] };
  }, [snapshotData, is_empty]);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    setNodes(rawNodes);
    setEdges(rawEdges);
  }, [rawNodes, rawEdges, setNodes, setEdges]);


  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  const onNodeClick = (_, node) => {
    setSelectedNode(node);
  };

  const filteredNodes = nodes.filter(n => {
    if (selectedType !== 'ALL' && (n.data.type || '').toUpperCase() !== selectedType) return false;
    if (search && !(n.data.label || '').toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, height: 'calc(100vh - 110px)', maxWidth: 1400 }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h1 style={{ fontSize: 22, fontWeight: 800, color: '#0F172A', margin: 0 }}>Knowledge Graph Digital Twin</h1>
            <span style={{ background: '#F1F5F9', color: '#475569', fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 10 }}>PostgreSQL Enforced</span>
          </div>
          <p style={{ fontSize: 13.5, color: '#64748B', marginTop: 4 }}>
            Real-time NetworkX digital twin graph auto-synchronized with PostgreSQL supply chain entities
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button 
            onClick={() => refetch()} 
            disabled={isLoading}
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#2563EB', color: 'white', border: 'none', borderRadius: 8, padding: '8px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} /> Sync Graph
          </button>
        </div>
      </motion.div>

      {/* Filter Chips Bar */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        {['ALL', 'COMPANY', 'FACTORY', 'WAREHOUSE', 'PRODUCT', 'COMPONENT', 'SUPPLIER', 'SHIPMENT', 'INCIDENT', 'RECOMMENDATION'].map(t => (
          <button
            key={t}
            onClick={() => setSelectedType(t)}
            style={{
              background: selectedType === t ? '#0F172A' : '#F8FAFC',
              color: selectedType === t ? 'white' : '#475569',
              border: '1px solid #E2E8F0',
              borderRadius: 20,
              padding: '5px 12px',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              textTransform: 'capitalize',
            }}
          >
            {t.toLowerCase()}
          </button>
        ))}
      </div>

      {/* Graph Canvas & Side Panel */}
      <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0, position: 'relative' }}>
        {/* Main Canvas */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
          {/* Search bar overlay */}
          <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 10, display: 'flex', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'white', border: '1px solid #CBD5E1', borderRadius: 8, padding: '7px 12px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
              <Search size={14} color="#64748B" />
              <input 
                value={search} 
                onChange={e => setSearch(e.target.value)} 
                placeholder="Search nodes by name..." 
                style={{ border: 'none', outline: 'none', fontSize: 13, width: 180, color: '#0F172A', background: 'transparent' }} 
              />
            </div>
          </div>

          {/* Professional Empty State Overlay */}
          {is_empty && !isLoading && (
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 10, textAlign: 'center', background: 'white', border: '1px solid #E2E8F0', borderRadius: 16, padding: '36px 44px', boxShadow: '0 12px 40px rgba(0,0,0,0.08)', maxWidth: 480 }}>
              <div style={{ width: 56, height: 56, background: '#EFF6FF', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                <Building2 size={28} color="#2563EB" />
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 800, color: '#0F172A', marginBottom: 8 }}>Digital Twin Knowledge Graph Empty</h3>
              <p style={{ fontSize: 13.5, color: '#64748B', lineHeight: 1.6, margin: 0 }}>
                {snapshotData?.empty_message || "No supply chain entities available. Complete your company setup and onboard suppliers to begin building your digital twin graph."}
              </p>
            </div>
          )}

          <ReactFlow
            nodes={filteredNodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-right"
          >
            <Background color="#E2E8F0" gap={24} size={1} />
            <Controls style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.08)', border: '1px solid #CBD5E1', borderRadius: 8 }} />
            <MiniMap style={{ border: '1px solid #CBD5E1', borderRadius: 8 }} nodeColor={n => colorMap[n.data?.type]?.border || '#CBD5E1'} />
          </ReactFlow>
        </motion.div>

        {/* Node Details Drawer */}
        <AnimatePresence>
          {selectedNode && (
            <motion.div 
              initial={{ opacity: 0, x: 50 }} 
              animate={{ opacity: 1, x: 0 }} 
              exit={{ opacity: 0, x: 50 }}
              className="card"
              style={{ width: 340, padding: 20, display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto', flexShrink: 0 }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #F1F5F9', paddingBottom: 12 }}>
                <div style={{ fontSize: 16, fontWeight: 800, color: '#0F172A' }}>Node Details</div>
                <button onClick={() => setSelectedNode(null)} style={{ background: '#F1F5F9', border: 'none', borderRadius: 6, width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
                  <X size={15} color="#64748B" />
                </button>
              </div>

              <div>
                <h3 style={{ fontSize: 16, fontWeight: 800, color: '#0F172A', marginBottom: 4 }}>{selectedNode.data.label}</h3>
                <span style={{ background: '#EFF6FF', color: '#2563EB', fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 6, textTransform: 'uppercase' }}>
                  {selectedNode.data.category || selectedNode.data.type}
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {Object.entries(selectedNode.data.details || {}).map(([key, val]) => (
                  <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, padding: '6px 0', borderBottom: '1px dashed #E2E8F0' }}>
                    <span style={{ color: '#64748B', fontWeight: 600 }}>{key}:</span>
                    <span style={{ color: '#0F172A', fontWeight: 700 }}>{String(val)}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
