import { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ReactFlow,
  MiniMap, Controls, Background,
  addEdge, useNodesState, useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Search, ZoomIn, AlertTriangle, Package, Cpu, Building2 } from 'lucide-react';

const colorMap = {
  supplier:  { bg: '#DBEAFE', border: '#93C5FD', text: '#1E40AF', icon: Building2 },
  component: { bg: '#D1FAE5', border: '#6EE7B7', text: '#065F46', icon: Cpu },
  product:   { bg: '#EDE9FE', border: '#C4B5FD', text: '#5B21B6', icon: Package },
  risk:      { bg: '#FEE2E2', border: '#FCA5A5', text: '#991B1B', icon: AlertTriangle },
};

function CustomNode({ data }) {
  const c = colorMap[data.type] || colorMap.supplier;
  const Icon = c.icon;
  return (
    <div style={{
      background: c.bg, border: `2px solid ${c.border}`, borderRadius: 10,
      padding: '10px 14px', minWidth: 140, boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      display: 'flex', alignItems: 'center', gap: 8, transition: 'box-shadow 0.2s',
    }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.12)'}
      onMouseLeave={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)'}
    >
      <div style={{ width: 28, height: 28, background: c.border, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={14} color={c.text} />
      </div>
      <div>
        <div style={{ fontSize: 12, fontWeight: 700, color: c.text, marginBottom: 1 }}>{data.label}</div>
        <div style={{ fontSize: 10, color: c.text, opacity: 0.7, textTransform: 'capitalize' }}>{data.type}</div>
      </div>
      {data.risk === 'critical' && (
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#DC2626', flexShrink: 0 }} />
      )}
    </div>
  );
}

const nodeTypes = { custom: CustomNode };

const initialNodes = [
  { id: '1', type: 'custom', position: { x: 400, y: 100 }, data: { label: 'Apple Inc.', type: 'product', risk: 'high' } },
  { id: '2', type: 'custom', position: { x: 150, y: 250 }, data: { label: 'TSMC', type: 'supplier', risk: 'critical' } },
  { id: '3', type: 'custom', position: { x: 650, y: 250 }, data: { label: 'Samsung', type: 'supplier', risk: 'low' } },
  { id: '4', type: 'custom', position: { x: 50,  y: 420 }, data: { label: 'A17 Pro Chip', type: 'component', risk: 'critical' } },
  { id: '5', type: 'custom', position: { x: 280, y: 420 }, data: { label: 'OLED Display', type: 'component', risk: 'low' } },
  { id: '6', type: 'custom', position: { x: 550, y: 420 }, data: { label: 'DRAM Memory', type: 'component', risk: 'medium' } },
  { id: '7', type: 'custom', position: { x: 750, y: 420 }, data: { label: 'Foxconn', type: 'supplier', risk: 'medium' } },
  { id: '8', type: 'custom', position: { x: 150, y: 580 }, data: { label: 'Taiwan Strait Disruption', type: 'risk', risk: 'critical' } },
  { id: '9', type: 'custom', position: { x: 500, y: 580 }, data: { label: 'Rotterdam Strike', type: 'risk', risk: 'high' } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', label: 'manufactures', animated: true, style: { stroke: '#93C5FD', strokeWidth: 2 } },
  { id: 'e1-3', source: '1', target: '3', label: 'manufactures', animated: false, style: { stroke: '#6EE7B7', strokeWidth: 2 } },
  { id: 'e2-4', source: '2', target: '4', label: 'produces', animated: true, style: { stroke: '#FCA5A5', strokeWidth: 2 } },
  { id: 'e2-5', source: '2', target: '5', label: 'produces', animated: false, style: { stroke: '#93C5FD', strokeWidth: 2 } },
  { id: 'e3-6', source: '3', target: '6', label: 'produces', animated: false, style: { stroke: '#6EE7B7', strokeWidth: 2 } },
  { id: 'e7-1', source: '7', target: '1', label: 'assembles', animated: false, style: { stroke: '#C4B5FD', strokeWidth: 2 } },
  { id: 'e8-2', source: '8', target: '2', label: 'impacts', animated: true, style: { stroke: '#FCA5A5', strokeWidth: 2, strokeDasharray: '5,5' } },
  { id: 'e8-4', source: '8', target: '4', label: 'disrupts', animated: true, style: { stroke: '#FCA5A5', strokeWidth: 2, strokeDasharray: '5,5' } },
  { id: 'e9-7', source: '9', target: '7', label: 'impacts', animated: true, style: { stroke: '#FCD34D', strokeWidth: 2, strokeDasharray: '5,5' } },
];

export default function KnowledgeGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [search, setSearch] = useState('');

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const highlightedNodes = search
    ? nodes.map(n => ({ ...n, style: n.data.label.toLowerCase().includes(search.toLowerCase()) ? { opacity: 1 } : { opacity: 0.3 } }))
    : nodes;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, height: 'calc(100vh - 110px)' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexShrink: 0, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Knowledge Graph</h1>
          <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Interactive supplier-component-product relationship visualization</p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {Object.entries(colorMap).map(([type, c]) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 5, background: c.bg, border: `1px solid ${c.border}`, borderRadius: 6, padding: '4px 10px', fontSize: 11, fontWeight: 600, color: c.text, textTransform: 'capitalize' }}>
              {type}
            </div>
          ))}
        </div>
      </motion.div>

      {/* Graph + Panel */}
      <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0 }}>
        {/* Graph */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="card" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}
        >
          {/* Search overlay */}
          <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 10, display: 'flex', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'white', border: '1px solid #E5E7EB', borderRadius: 8, padding: '7px 12px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
              <Search size={14} color="#9CA3AF" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search nodes..." style={{ border: 'none', outline: 'none', fontSize: 13, width: 160, color: '#374151', background: 'transparent' }} />
            </div>
          </div>

          <ReactFlow
            nodes={highlightedNodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-right"
          >
            <Background color="#E5E7EB" gap={24} size={1} />
            <Controls style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.08)', border: '1px solid #E5E7EB', borderRadius: 8 }} />
            <MiniMap style={{ border: '1px solid #E5E7EB', borderRadius: 8 }} nodeColor={n => colorMap[n.data?.type]?.border || '#E5E7EB'} />
          </ReactFlow>
        </motion.div>

        {/* Legend & Stats */}
        <motion.div initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
          className="card" style={{ width: 240, padding: 16, display: 'flex', flexDirection: 'column', gap: 16, overflow: 'auto', flexShrink: 0 }}
        >
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', marginBottom: 12 }}>Graph Stats</div>
            {[{ label: 'Total Nodes', value: initialNodes.length }, { label: 'Relationships', value: initialEdges.length }, { label: 'Critical Paths', value: 3 }, { label: 'At-Risk Nodes', value: 4 }].map(s => (
              <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #F3F4F6', fontSize: 13 }}>
                <span style={{ color: '#6B7280' }}>{s.label}</span>
                <span style={{ fontWeight: 700, color: '#111827' }}>{s.value}</span>
              </div>
            ))}
          </div>

          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', marginBottom: 10 }}>Active Disruptions</div>
            {initialNodes.filter(n => n.data.type === 'risk').map(n => (
              <div key={n.id} style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 7, padding: '8px 10px', marginBottom: 6 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#991B1B' }}>{n.data.label}</div>
                <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2 }}>Propagating through graph</div>
              </div>
            ))}
          </div>

          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', marginBottom: 10 }}>Instructions</div>
            <div style={{ fontSize: 11.5, color: '#9CA3AF', lineHeight: 1.7 }}>
              • Drag nodes to reposition<br />
              • Scroll to zoom in/out<br />
              • Click node for details<br />
              • Use minimap to navigate<br />
              • Search to highlight nodes
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
