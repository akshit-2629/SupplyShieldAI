import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X } from 'lucide-react';

/**
 * ConfirmDialog — modal confirmation dialog.
 * @param {boolean} open
 * @param {string} title
 * @param {string} description
 * @param {string} [confirmLabel='Confirm']
 * @param {string} [cancelLabel='Cancel']
 * @param {'danger'|'warning'|'default'} [variant='default']
 * @param {function} onConfirm
 * @param {function} onCancel
 * @param {boolean} [loading]
 */
export default function ConfirmDialog({ open, title, description, confirmLabel = 'Confirm', cancelLabel = 'Cancel', variant = 'default', onConfirm, onCancel, loading }) {
  const colors = {
    danger: { bg: '#EF4444', hover: '#DC2626', icon: '#EF4444', iconBg: '#FEF2F2' },
    warning: { bg: '#F59E0B', hover: '#D97706', icon: '#F59E0B', iconBg: '#FFFBEB' },
    default: { bg: '#2563EB', hover: '#1D4ED8', icon: '#2563EB', iconBg: '#EFF6FF' },
  };
  const c = colors[variant];

  return (
    <AnimatePresence>
      {open && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="modal-backdrop" style={{ zIndex: 100 }}>
          <motion.div initial={{ opacity: 0, scale: 0.92, y: 16 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.92, y: 16 }} transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
            style={{ background: 'white', borderRadius: 16, padding: '28px 28px 24px', width: '100%', maxWidth: 420, boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}
          >
            <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: c.iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <AlertTriangle size={22} color={c.icon} />
              </div>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: '#111827', marginBottom: 4 }}>{title}</h3>
                <p style={{ fontSize: 13, color: '#6B7280', lineHeight: 1.6 }}>{description}</p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button onClick={onCancel} disabled={loading}
                style={{ padding: '9px 20px', border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 13, fontWeight: 600, background: 'white', color: '#374151', cursor: 'pointer' }}>
                {cancelLabel}
              </button>
              <button onClick={onConfirm} disabled={loading}
                style={{ padding: '9px 20px', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 700, background: c.bg, color: 'white', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}>
                {loading ? 'Processing...' : confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
