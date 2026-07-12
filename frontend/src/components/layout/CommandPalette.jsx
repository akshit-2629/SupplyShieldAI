import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Command, Search, LayoutDashboard, AlertTriangle, Globe, Network, Building2, Cpu, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../../store/appStore';

const commands = [
  { label: 'Dashboard', icon: LayoutDashboard, to: '/dashboard', group: 'Pages' },
  { label: 'Disruption Monitor', icon: AlertTriangle, to: '/disruption-monitor', group: 'Pages' },
  { label: 'Global Risk Map', icon: Globe, to: '/risk-map', group: 'Pages' },
  { label: 'Knowledge Graph', icon: Network, to: '/knowledge-graph', group: 'Pages' },
  { label: 'Suppliers', icon: Building2, to: '/suppliers', group: 'Pages' },
  { label: 'AI Orchestration', icon: Cpu, to: '/orchestration', group: 'Pages' },
  { label: 'Reports', icon: FileText, to: '/reports', group: 'Pages' },
];

export default function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useAppStore();
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const filtered = commands.filter(c => c.label.toLowerCase().includes(query.toLowerCase()));

  function handleSelect(to) {
    navigate(to);
    setCommandPaletteOpen(false);
    setQuery('');
  }

  return (
    <AnimatePresence>
      {commandPaletteOpen && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="modal-backdrop" onClick={() => setCommandPaletteOpen(false)}
        >
          <motion.div initial={{ opacity: 0, y: -20, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -20, scale: 0.96 }} transition={{ duration: 0.2 }}
            style={{ width: 560, background: 'white', borderRadius: 14, boxShadow: '0 20px 60px rgba(0,0,0,0.15)', border: '1px solid #E5E7EB', overflow: 'hidden' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', borderBottom: '1px solid #F3F4F6' }}>
              <Search size={16} color="#9CA3AF" />
              <input autoFocus value={query} onChange={e => setQuery(e.target.value)}
                placeholder="Search pages, actions..."
                style={{ flex: 1, border: 'none', outline: 'none', fontSize: 14, color: '#111827', background: 'transparent' }}
                onKeyDown={e => { if (e.key === 'Escape') setCommandPaletteOpen(false); if (e.key === 'Enter' && filtered[0]) handleSelect(filtered[0].to); }}
              />
              <kbd style={{ background: '#F3F4F6', border: '1px solid #E5E7EB', borderRadius: 4, padding: '2px 6px', fontSize: 11, color: '#9CA3AF' }}>ESC</kbd>
            </div>
            <div style={{ maxHeight: 380, overflowY: 'auto', padding: 8 }}>
              {filtered.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '32px 16px', color: '#9CA3AF', fontSize: 14 }}>No results found</div>
              ) : (
                filtered.map(cmd => (
                  <button key={cmd.to} onClick={() => handleSelect(cmd.to)}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', borderRadius: 8, border: 'none', background: 'none', cursor: 'pointer', fontSize: 14, color: '#374151', textAlign: 'left', transition: 'background 0.1s' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#F5F5F5'}
                    onMouseLeave={e => e.currentTarget.style.background = 'none'}
                  >
                    <div style={{ width: 30, height: 30, background: '#EFF6FF', borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <cmd.icon size={15} color="#2563EB" />
                    </div>
                    {cmd.label}
                  </button>
                ))
              )}
            </div>
            <div style={{ padding: '10px 16px', borderTop: '1px solid #F3F4F6', display: 'flex', gap: 16, fontSize: 11, color: '#9CA3AF' }}>
              <span>↵ Select</span><span>↑↓ Navigate</span><span>ESC Close</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
