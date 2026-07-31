import { useState, useRef } from 'react';
import { Upload, X, File, Image } from 'lucide-react';

/**
 * FileUploadZone — drag-and-drop file input.
 * @param {function} onFiles - called with FileList
 * @param {string[]} [accept] - MIME types
 * @param {boolean} [multiple]
 * @param {string} [hint]
 */
export default function FileUploadZone({ onFiles, accept = [], multiple = false, hint = 'Drag & drop files here, or click to browse' }) {
  const [dragging, setDragging] = useState(false);
  const [files, setFiles] = useState([]);
  const inputRef = useRef(null);

  function handleFiles(incoming) {
    const arr = Array.from(incoming);
    setFiles((prev) => multiple ? [...prev, ...arr] : arr);
    onFiles?.(incoming);
  }

  function removeFile(i) {
    setFiles((prev) => prev.filter((_, idx) => idx !== i));
  }

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
        style={{
          border: `2px dashed ${dragging ? '#2563EB' : '#E5E7EB'}`,
          borderRadius: 12,
          padding: '32px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          background: dragging ? '#EFF6FF' : '#FAFAFA',
          transition: 'all 0.2s',
        }}
      >
        <div style={{ width: 44, height: 44, borderRadius: 12, background: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
          <Upload size={20} color="#9CA3AF" />
        </div>
        <p style={{ fontSize: 13, color: '#374151', fontWeight: 500, marginBottom: 4 }}>{hint}</p>
        {accept.length > 0 && <p style={{ fontSize: 11, color: '#9CA3AF' }}>Accepted: {accept.join(', ')}</p>}
        <input ref={inputRef} type="file" multiple={multiple} accept={accept.join(',')} style={{ display: 'none' }} onChange={(e) => handleFiles(e.target.files)} />
      </div>

      {files.length > 0 && (
        <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {files.map((f, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 8, padding: '8px 12px' }}>
              {f.type.startsWith('image') ? <Image size={16} color="#6B7280" /> : <File size={16} color="#6B7280" />}
              <span style={{ fontSize: 13, color: '#374151', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
              <span style={{ fontSize: 11, color: '#9CA3AF' }}>{(f.size / 1024).toFixed(0)}KB</span>
              <button onClick={(e) => { e.stopPropagation(); removeFile(i); }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF', padding: 0 }}>
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
