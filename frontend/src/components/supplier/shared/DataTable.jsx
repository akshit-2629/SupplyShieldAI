import { useState, useMemo } from 'react';
import { Search, ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import EmptyState from './EmptyState';
import { SkeletonTable } from './SkeletonCard';

/**
 * DataTable — responsive table with sort, search, pagination.
 * @param {Array} columns - [{ key, label, render?, sortable?, width? }]
 * @param {Array} data
 * @param {boolean} [loading]
 * @param {boolean} [searchable]
 * @param {number} [pageSize=10]
 * @param {string} [emptyTitle]
 * @param {string} [emptyDescription]
 */
export default function DataTable({
  columns = [],
  data = [],
  loading = false,
  searchable = true,
  pageSize = 10,
  emptyTitle = 'No data found',
  emptyDescription,
  onRowClick,
}) {
  const [query, setQuery] = useState('');
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    if (!query.trim()) return data;
    const q = query.toLowerCase();
    return data.filter((row) => Object.values(row).some((v) => String(v).toLowerCase().includes(q)));
  }, [data, query]);

  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => {
      const av = a[sortKey]; const bv = b[sortKey];
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const paged = sorted.slice((page - 1) * pageSize, page * pageSize);

  function handleSort(key) {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
    setPage(1);
  }

  function SortIcon({ col }) {
    if (!col.sortable) return null;
    if (sortKey !== col.key) return <ChevronsUpDown size={12} color="#D1D5DB" />;
    return sortDir === 'asc' ? <ChevronUp size={12} color="#2563EB" /> : <ChevronDown size={12} color="#2563EB" />;
  }

  return (
    <div>
      {searchable && (
        <div style={{ marginBottom: 16, position: 'relative', maxWidth: 320 }}>
          <Search size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#9CA3AF' }} />
          <input
            value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }}
            placeholder="Search..."
            style={{ width: '100%', paddingLeft: 36, paddingRight: 12, paddingTop: 9, paddingBottom: 9, border: '1px solid #E5E7EB', borderRadius: 8, fontSize: 13, outline: 'none', boxSizing: 'border-box' }}
            onFocus={(e) => { e.target.style.borderColor = '#2563EB'; }}
            onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; }}
          />
        </div>
      )}

      {loading ? (
        <SkeletonTable rows={5} cols={columns.length} />
      ) : paged.length === 0 ? (
        <EmptyState type="search" title={emptyTitle} description={emptyDescription} />
      ) : (
        <>
          {/* Desktop table */}
          <div style={{ overflowX: 'auto' }} className="hidden-mobile">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #F3F4F6' }}>
                  {columns.map((col) => (
                    <th key={col.key}
                      onClick={() => col.sortable && handleSort(col.key)}
                      style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: '#6B7280', letterSpacing: '0.05em', textTransform: 'uppercase', cursor: col.sortable ? 'pointer' : 'default', whiteSpace: 'nowrap', width: col.width, userSelect: 'none' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        {col.label}
                        <SortIcon col={col} />
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paged.map((row, i) => (
                  <tr key={row.id ?? i}
                    onClick={() => onRowClick?.(row)}
                    style={{ borderBottom: '1px solid #F9FAFB', cursor: onRowClick ? 'pointer' : 'default', transition: 'background 0.1s' }}
                    onMouseEnter={(e) => { if (onRowClick) e.currentTarget.style.background = '#F9FAFB'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                  >
                    {columns.map((col) => (
                      <td key={col.key} style={{ padding: '12px 16px', color: '#374151', verticalAlign: 'middle' }}>
                        {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 16, flexWrap: 'wrap', gap: 8 }}>
              <span style={{ fontSize: 12, color: '#9CA3AF' }}>
                Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, sorted.length)} of {sorted.length}
              </span>
              <div style={{ display: 'flex', gap: 4 }}>
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
                  style={{ padding: '5px 12px', border: '1px solid #E5E7EB', borderRadius: 6, fontSize: 12, background: 'white', cursor: page === 1 ? 'not-allowed' : 'pointer', color: page === 1 ? '#D1D5DB' : '#374151' }}>
                  Prev
                </button>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => i + 1).map((p) => (
                  <button key={p} onClick={() => setPage(p)}
                    style={{ padding: '5px 10px', border: '1px solid', borderColor: page === p ? '#2563EB' : '#E5E7EB', borderRadius: 6, fontSize: 12, background: page === p ? '#2563EB' : 'white', color: page === p ? 'white' : '#374151', cursor: 'pointer', fontWeight: page === p ? 700 : 400 }}>
                    {p}
                  </button>
                ))}
                <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                  style={{ padding: '5px 12px', border: '1px solid #E5E7EB', borderRadius: 6, fontSize: 12, background: 'white', cursor: page === totalPages ? 'not-allowed' : 'pointer', color: page === totalPages ? '#D1D5DB' : '#374151' }}>
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
