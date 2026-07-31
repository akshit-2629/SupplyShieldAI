import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Building2, MapPin, Phone, Mail, Globe, Award, FileText, Plus, Edit3, Save, X, Upload, Trash2, ExternalLink, CheckCircle2, Download, Loader } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/supplier/shared/PageHeader';
import StatusBadge from '../../components/supplier/shared/StatusBadge';
import FileUploadZone from '../../components/supplier/shared/FileUploadZone';
import { useSupplierAuth } from '../../context/SupplierAuthContext';
import { updateSupplierProfile, getSupplierProfile, getDocuments, uploadDocument, deleteDocument } from '../../services/supplierApi';
import { downloadFile } from '../../lib/utils';

function Section({ title, icon: Icon, children, onEdit, editing, onSave, onCancel, saving }) {
  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div style={{ padding: '18px 24px', borderBottom: '1px solid #F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {Icon && <div style={{ width: 32, height: 32, background: '#ECFDF5', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Icon size={16} color="#10B981" /></div>}
          <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>{title}</h3>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {editing ? (
            <>
              <button onClick={onCancel} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '6px 14px', border: '1px solid #E5E7EB', borderRadius: 7, fontSize: 12, background: 'white', color: '#374151', cursor: 'pointer', fontWeight: 600 }}>
                <X size={13} /> Cancel
              </button>
              <button onClick={onSave} disabled={saving} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '6px 14px', border: 'none', borderRadius: 7, fontSize: 12, background: '#10B981', color: 'white', cursor: 'pointer', fontWeight: 600, opacity: saving ? 0.7 : 1 }}>
                <Save size={13} /> {saving ? 'Saving…' : 'Save'}
              </button>
            </>
          ) : (
            onEdit && (
              <button onClick={onEdit} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '6px 14px', border: '1px solid #E5E7EB', borderRadius: 7, fontSize: 12, background: 'white', color: '#374151', cursor: 'pointer', fontWeight: 600 }}>
                <Edit3 size={13} /> Edit
              </button>
            )
          )}
        </div>
      </div>
      <div style={{ padding: '20px 24px' }}>{children}</div>
    </div>
  );
}

function Field({ label, value, type = 'text', editing, onChange, placeholder, span = 1 }) {
  return (
    <div style={{ gridColumn: `span ${span}` }}>
      <label style={{ fontSize: 11, fontWeight: 600, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 6 }}>{label}</label>
      {editing ? (
        <input type={type} value={value || ''} onChange={(e) => onChange(e.target.value)} placeholder={placeholder || label}
          style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '8px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box' }}
          onFocus={(e) => { e.target.style.borderColor = '#10B981'; }}
          onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; }}
        />
      ) : (
        <div style={{ fontSize: 14, color: value ? '#111827' : '#9CA3AF', fontWeight: value ? 500 : 400 }}>{value || '—'}</div>
      )}
    </div>
  );
}

export default function CompanyProfile() {
  const navigate = useNavigate();
  const { supplierUser } = useSupplierAuth();
  const meta = supplierUser?.user_metadata || {};

  const [editingBasic, setEditingBasic] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const [basic, setBasic] = useState({
    companyName: meta.companyName || meta.company_name || '',
    legalName: meta.legalName || meta.legal_name || '',
    website: meta.website || '',
    phone: meta.phone || '',
    email: supplierUser?.email || '',
    country: meta.country || meta.headquarters_country || '',
    industry: meta.industry || (meta.manufacturing_categories?.[0]) || '',
    founded: '',
    employees: '',
    description: '',
  });

  // Locations state — defaults to empty
  const [locations, setLocations] = useState([]);
  const [showAddLocation, setShowAddLocation] = useState(false);
  const [newLoc, setNewLoc] = useState({ name: '', type: 'Factory', city: '', country: '' });

  // Certifications state — defaults to empty (no fake mock data)
  const [certifications, setCertifications] = useState([]);
  const [showAddCert, setShowAddCert] = useState(false);
  const [newCertName, setNewCertName] = useState('');

  // Documents state & file upload
  const [documents, setDocuments] = useState([]);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const fileInputRef = useRef(null);
  const [targetDocType, setTargetDocType] = useState('COMPLIANCE');

  useEffect(() => {
    async function load() {
      try {
        const p = await getSupplierProfile();
        if (p) {
          setBasic((prev) => ({
            ...prev,
            companyName: p.company_name || prev.companyName,
            legalName: p.legal_name || prev.legalName,
            website: p.website || prev.website,
            phone: p.phone || prev.phone,
            email: p.email || prev.email,
            country: p.headquarters_country || prev.country,
            industry: p.manufacturing_categories?.[0] || prev.industry,
            founded: p.year_established ? String(p.year_established) : prev.founded,
            employees: p.employee_count ? String(p.employee_count) : prev.employees,
            description: p.description || prev.description,
          }));
          if (Array.isArray(p.locations)) {
            setLocations(p.locations);
          }
          if (Array.isArray(p.certifications)) {
            setCertifications(p.certifications.map(c => typeof c === 'string' ? c : c.name));
          }
        }
      } catch (_) {}

      try {
        const docRes = await getDocuments();
        const docList = Array.isArray(docRes) ? docRes : (docRes?.data || docRes?.items || []);
        setDocuments(docList);
      } catch (_) {}
    }
    load();
  }, []);


  async function saveBasic() {
    setSaving(true);
    setErrorMsg('');
    try {
      await updateSupplierProfile({
        company_name: basic.companyName,
        legal_name: basic.legalName,
        website: basic.website,
        phone: basic.phone,
        email: basic.email,
        headquarters_country: basic.country,
        manufacturing_categories: basic.industry ? [basic.industry] : [],
        year_established: basic.founded ? (parseInt(basic.founded, 10) || null) : null,
        employee_count: basic.employees ? (parseInt(basic.employees, 10) || null) : null,
        description: basic.description,
        locations,
        certifications: certifications.map(c => typeof c === 'string' ? { name: c } : c),
      });
      setEditingBasic(false);
      load();
    } catch (err) {
      console.error('Save basic failed:', err);
      setErrorMsg(err.message || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  }

  // Location handlers
  async function handleAddLocation(e) {
    e.preventDefault();
    if (!newLoc.name) return;
    const updated = [...locations, newLoc];
    setLocations(updated);
    setNewLoc({ name: '', type: 'Factory', city: '', country: '' });
    setShowAddLocation(false);
    try {
      await updateSupplierProfile({ locations: updated });
    } catch (_) {}
  }

  async function handleDeleteLocation(index) {
    const updated = locations.filter((_, i) => i !== index);
    setLocations(updated);
    try {
      await updateSupplierProfile({ locations: updated });
    } catch (_) {}
  }

  // Certification handlers
  async function handleAddCertification(e) {
    e.preventDefault();
    if (!newCertName.trim()) return;
    const updated = [...certifications, newCertName.trim()];
    setCertifications(updated);
    setNewCertName('');
    setShowAddCert(false);
    try {
      await updateSupplierProfile({ certifications: updated.map(c => ({ name: c })) });
    } catch (_) {}
  }

  async function handleDeleteCert(certName) {
    const updated = certifications.filter(c => c !== certName);
    setCertifications(updated);
    try {
      await updateSupplierProfile({ certifications: updated.map(c => ({ name: c })) });
    } catch (_) {}
  }

  // Document upload handler
  async function handleFileUpload(files, docInfo) {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploadingDoc(true);
    setErrorMsg('');
    const category = typeof docInfo === 'object' ? docInfo.category : 'COMPLIANCE';
    const title = typeof docInfo === 'object' ? docInfo.name : docInfo;
    try {
      await uploadDocument(file, {
        category: category || 'COMPLIANCE',
        title: title || file.name,
        display_name: title || file.name,
      });
      const docRes = await getDocuments();
      const docList = Array.isArray(docRes) ? docRes : (docRes?.data || docRes?.items || []);
      setDocuments(docList);
    } catch (err) {
      console.error('Document upload failed:', err);
      setErrorMsg(err.message || 'Document upload failed');
    } finally {
      setUploadingDoc(false);
    }
  }

  function triggerDocUpload(docName) {
    const category = docName.includes('Tax') ? 'TAX_ID' : (docName.includes('Registration') ? 'BUSINESS_REGISTRATION' : 'COMPLIANCE');
    setTargetDocType({ name: docName, category });
    if (fileInputRef.current) fileInputRef.current.click();
  }

  const setField = (f) => (v) => setBasic((p) => ({ ...p, [f]: v }));

  const grid3 = { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px 20px' };

  return (
    <div>
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={(e) => {
          if (e.target.files?.length) {
            handleFileUpload(e.target.files, targetDocType);
            e.target.value = '';
          }
        }}
      />

      <PageHeader
        title="Company Profile"
        description="Manage your organization's information, certifications, and documents"
        actions={
          <StatusBadge status="approved" label="Profile Active" />
        }
      />

      {/* Logo Upload */}
      <div className="card" style={{ marginBottom: 20, padding: '20px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
          <div style={{ width: 80, height: 80, borderRadius: 16, background: 'linear-gradient(135deg, #10B981, #059669)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, fontWeight: 800, color: 'white', flexShrink: 0 }}>
            {(basic.companyName || meta.companyName || 'S')[0].toUpperCase()}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: '#111827', marginBottom: 4 }}>{basic.companyName || meta.companyName || 'Company Name'}</div>
            <div style={{ fontSize: 13, color: '#6B7280', marginBottom: 12 }}>{basic.industry || 'Electronics'} · {basic.country || 'UK'}</div>
            <button style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 16px', border: '1px solid #E5E7EB', borderRadius: 7, fontSize: 12, fontWeight: 600, background: 'white', color: '#374151', cursor: 'pointer' }}>
              <Upload size={13} /> Upload Logo
            </button>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <StatusBadge status="approved" />
            <div style={{ fontSize: 12, color: '#6B7280' }}>Supplier since {new Date().getFullYear()}</div>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', color: '#DC2626', padding: '10px 16px', borderRadius: 8, fontSize: 13, marginBottom: 16 }}>
          {errorMsg}
        </div>
      )}

      {/* Basic Info */}
      <Section title="Company Information" icon={Building2} onEdit={() => setEditingBasic(true)} editing={editingBasic} onSave={saveBasic} onCancel={() => setEditingBasic(false)} saving={saving}>
        <div style={grid3}>
          <Field label="Company Name" value={basic.companyName} editing={editingBasic} onChange={setField('companyName')} />
          <Field label="Legal Business Name" value={basic.legalName} editing={editingBasic} onChange={setField('legalName')} />
          <Field label="Industry" value={basic.industry} editing={editingBasic} onChange={setField('industry')} />
          <Field label="Country" value={basic.country} editing={editingBasic} onChange={setField('country')} />
          <Field label="Phone" value={basic.phone} editing={editingBasic} onChange={setField('phone')} />
          <Field label="Email" value={basic.email} editing={editingBasic} onChange={setField('email')} type="email" />
          <Field label="Website" value={basic.website} editing={editingBasic} onChange={setField('website')} />
          <Field label="Founded Year" value={basic.founded} editing={editingBasic} onChange={setField('founded')} placeholder="YYYY" />
          <Field label="Number of Employees" value={basic.employees} editing={editingBasic} onChange={setField('employees')} />
        </div>
        {editingBasic && (
          <div style={{ marginTop: 16 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 6 }}>Company Description</label>
            <textarea value={basic.description} onChange={(e) => setBasic((p) => ({ ...p, description: e.target.value }))}
              placeholder="Brief description of your company and services..."
              rows={3}
              style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '8px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box', resize: 'vertical' }}
              onFocus={(e) => { e.target.style.borderColor = '#10B981'; }}
              onBlur={(e) => { e.target.style.borderColor = '#E5E7EB'; }}
            />
          </div>
        )}
      </Section>

      {/* Factory & Warehouse Locations */}
      <Section title="Factory & Warehouse Locations" icon={MapPin}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {locations.map((loc, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px', background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 10 }}>
              <div style={{ width: 36, height: 36, borderRadius: 8, background: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <MapPin size={16} color="#2563EB" />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13.5, fontWeight: 600, color: '#111827' }}>{loc.name || loc.label}</div>
                <div style={{ fontSize: 12, color: '#6B7280' }}>
                  {[loc.type, loc.city, loc.country].filter(Boolean).join(' · ') || 'Active Facility'}
                </div>
              </div>
              <StatusBadge status="approved" label="Active" />
              <button onClick={() => handleDeleteLocation(idx)} title="Delete location" style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 6, color: '#9CA3AF' }}>
                <Trash2 size={14} />
              </button>
            </div>
          ))}

          {locations.length === 0 && !showAddLocation && (
            <div style={{ padding: '14px 16px', background: '#F9FAFB', border: '1px dashed #D1D5DB', borderRadius: 10, fontSize: 12.5, color: '#6B7280', textAlign: 'center' }}>
              No factory or warehouse locations listed yet. Click <strong>+ Add Location</strong> to add facilities.
            </div>
          )}

          {showAddLocation ? (
            <form onSubmit={handleAddLocation} style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 10, padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 10 }}>
                <input
                  placeholder="Facility Name (e.g. Factory A)"
                  value={newLoc.name} onChange={(e) => setNewLoc({ ...newLoc, name: e.target.value })}
                  style={{ border: '1px solid #CBD5E1', borderRadius: 6, padding: '6px 10px', fontSize: 13 }}
                  required
                />
                <select
                  value={newLoc.type} onChange={(e) => setNewLoc({ ...newLoc, type: e.target.value })}
                  style={{ border: '1px solid #CBD5E1', borderRadius: 6, padding: '6px 10px', fontSize: 13, background: 'white' }}
                >
                  <option value="Factory">Factory</option>
                  <option value="Warehouse">Warehouse</option>
                  <option value="Office">Office</option>
                </select>
                <input
                  placeholder="City"
                  value={newLoc.city} onChange={(e) => setNewLoc({ ...newLoc, city: e.target.value })}
                  style={{ border: '1px solid #CBD5E1', borderRadius: 6, padding: '6px 10px', fontSize: 13 }}
                />
                <input
                  placeholder="Country"
                  value={newLoc.country} onChange={(e) => setNewLoc({ ...newLoc, country: e.target.value })}
                  style={{ border: '1px solid #CBD5E1', borderRadius: 6, padding: '6px 10px', fontSize: 13 }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                <button type="button" onClick={() => setShowAddLocation(false)} style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #CBD5E1', background: 'white', fontSize: 12, cursor: 'pointer' }}>Cancel</button>
                <button type="submit" style={{ padding: '6px 14px', borderRadius: 6, border: 'none', background: '#10B981', color: 'white', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>Save Location</button>
              </div>
            </form>
          ) : (
            <button onClick={() => setShowAddLocation(true)} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', border: '2px dashed #E5E7EB', borderRadius: 10, fontSize: 13, color: '#6B7280', background: 'transparent', cursor: 'pointer', fontWeight: 500, width: '100%', justifyContent: 'center' }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#10B981'; e.currentTarget.style.color = '#10B981'; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#E5E7EB'; e.currentTarget.style.color = '#6B7280'; }}
            >
              <Plus size={16} /> Add Location
            </button>
          )}
        </div>
      </Section>

      {/* Certifications */}
      <Section title="Certifications" icon={Award}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
          {certifications.map((cert) => {
            const certName = typeof cert === 'string' ? cert : cert.name;
            return (
              <div key={certName} style={{ display: 'flex', alignItems: 'center', justifyBetween: 'space-between', gap: 10, padding: '12px 14px', background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 10 }}>
                <div style={{ width: 30, height: 30, borderRadius: 8, background: '#ECFDF5', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Award size={15} color="#10B981" />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#111827', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{certName}</div>
                  <div style={{ fontSize: 11, color: '#10B981', fontWeight: 600 }}>Active Verified</div>
                </div>
                <button onClick={() => handleDeleteCert(certName)} title="Remove certification" style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, color: '#9CA3AF' }}>
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })}

          {certifications.length === 0 && !showAddCert && (
            <div style={{ gridColumn: '1 / -1', padding: '14px 16px', background: '#F9FAFB', border: '1px dashed #D1D5DB', borderRadius: 10, fontSize: 12.5, color: '#6B7280', textAlign: 'center' }}>
              No certifications uploaded or added yet. Click <strong>+ Add Certification</strong> to list ISO or quality standards.
            </div>
          )}

          {showAddCert ? (
            <form onSubmit={handleAddCertification} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: 6, border: '1px solid #10B981', borderRadius: 10, background: 'white' }}>
              <input
                placeholder="Certification Name"
                value={newCertName} onChange={(e) => setNewCertName(e.target.value)}
                style={{ border: 'none', outline: 'none', fontSize: 12, padding: '4px 8px', flex: 1 }}
                autoFocus
                required
              />
              <button type="submit" style={{ background: '#10B981', color: 'white', border: 'none', borderRadius: 6, padding: '4px 8px', fontSize: 11, fontWeight: 600, cursor: 'pointer' }}>Add</button>
              <button type="button" onClick={() => setShowAddCert(false)} style={{ background: 'none', border: 'none', color: '#6B7280', cursor: 'pointer', padding: 2 }}><X size={14} /></button>
            </form>
          ) : (
            <button onClick={() => setShowAddCert(true)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, padding: '12px', border: '2px dashed #E5E7EB', borderRadius: 10, fontSize: 12.5, color: '#6B7280', background: 'transparent', cursor: 'pointer', fontWeight: 500 }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#10B981'; e.currentTarget.style.color = '#10B981'; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#E5E7EB'; e.currentTarget.style.color = '#6B7280'; }}
            >
              <Plus size={15} /> Add Certification
            </button>
          )}
        </div>
      </Section>

      {/* Business Documents */}
      <Section title="Business Documents" icon={FileText}>
        <div style={{ marginBottom: 16 }}>
          <FileUploadZone
            hint="Upload business registration, licenses, tax documents, or compliance files"
            accept={['.pdf', '.doc', '.docx', '.png', '.jpg']}
            multiple
            onFilesSelected={(files) => handleFileUpload(files, 'Compliance Document')}
          />
        </div>

        {uploadingDoc && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', background: '#EFF6FF', borderRadius: 8, marginBottom: 12, fontSize: 13, color: '#2563EB' }}>
            <Loader size={16} className="animate-spin" /> Uploading document to secure vault…
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Required document templates */}
          {['Business Registration Certificate', 'Tax Identification Document'].map((docName) => {
            const uploaded = documents.find(d => {
              const title = (d.title || d.display_name || d.name || d.file_name || '').toLowerCase();
              const category = (d.category || '').toLowerCase();
              if (docName.includes('Registration')) {
                return title.includes('registration') || title.includes('business') || category === 'business_registration';
              }
              if (docName.includes('Tax')) {
                return title.includes('tax') || title.includes('vat') || category === 'tax_id';
              }
              return title.includes(docName.toLowerCase());
            });

            return (
              <div key={docName} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 10 }}>
                <FileText size={16} color={uploaded ? '#10B981' : '#6B7280'} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13.5, fontWeight: 600, color: '#111827' }}>{docName}</div>
                  {uploaded && <div style={{ fontSize: 11, color: '#6B7280' }}>Uploaded: {uploaded.display_name || uploaded.file_name || uploaded.name}</div>}
                </div>
                <StatusBadge status={uploaded ? 'approved' : 'pending'} label={uploaded ? 'Uploaded' : 'Not Uploaded'} />
                <button
                  onClick={() => triggerDocUpload(docName)}
                  style={{ padding: '6px 14px', border: '1px solid #E5E7EB', borderRadius: 7, fontSize: 12, background: 'white', color: '#374151', cursor: 'pointer', fontWeight: 600 }}
                >
                  {uploaded ? 'Re-upload' : 'Upload'}
                </button>
              </div>
            );
          })}

          {/* Uploaded documents list */}
          {documents.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', marginBottom: 8 }}>Uploaded Documents ({documents.length})</div>
              {documents.map((d) => (
                <div key={d.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderBottom: '1px solid #F3F4F6' }}>
                  <CheckCircle2 size={15} color="#10B981" />
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#111827', flex: 1 }}>{d.display_name || d.title || d.name || d.file_name}</span>
                  <span style={{ fontSize: 11, color: '#9CA3AF' }}>{d.category || 'DOCUMENT'}</span>
                  {(d.public_url || d.file_url) && (
                    <button onClick={() => downloadFile(d.public_url || d.file_url, d.display_name || d.title || d.name || d.file_name)}
                      style={{ fontSize: 12, color: '#2563EB', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Download size={13} /> Download
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 12 }}>
            <button
              onClick={() => navigate('/supplier/documents')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, color: '#10B981', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Manage all documents in Document Center <ExternalLink size={14} />
            </button>
          </div>
        </div>
      </Section>
    </div>
  );
}


