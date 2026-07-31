import { motion } from 'framer-motion';
import { Inbox, AlertCircle, SearchX, PackageOpen, FileX } from 'lucide-react';

const ICONS = {
  inbox: Inbox,
  error: AlertCircle,
  search: SearchX,
  package: PackageOpen,
  file: FileX,
};

/**
 * EmptyState — illustrated empty/error state with optional action button.
 * @param {string} [type='inbox'] - icon variant: inbox | error | search | package | file
 * @param {string} title
 * @param {string} [description]
 * @param {string} [actionLabel]
 * @param {function} [onAction]
 */
export default function EmptyState({ type = 'inbox', title, description, actionLabel, onAction }) {
  const Icon = ICONS[type] || Inbox;
  const iconColors = { inbox: '#9CA3AF', error: '#EF4444', search: '#9CA3AF', package: '#9CA3AF', file: '#9CA3AF' };
  const iconBgs = { inbox: '#F3F4F6', error: '#FEF2F2', search: '#F3F4F6', package: '#F3F4F6', file: '#F3F4F6' };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 24px', textAlign: 'center' }}
    >
      <div style={{ width: 72, height: 72, borderRadius: 20, background: iconBgs[type], display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
        <Icon size={32} color={iconColors[type]} strokeWidth={1.5} />
      </div>
      <h3 style={{ fontSize: 16, fontWeight: 700, color: '#111827', marginBottom: 8 }}>{title}</h3>
      {description && <p style={{ fontSize: 13, color: '#6B7280', maxWidth: 340, lineHeight: 1.6, marginBottom: 24 }}>{description}</p>}
      {actionLabel && onAction && (
        <button onClick={onAction} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: '#2563EB', color: 'white', border: 'none', borderRadius: 8, padding: '9px 20px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
          {actionLabel}
        </button>
      )}
    </motion.div>
  );
}
