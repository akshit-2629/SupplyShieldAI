import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Building2, Factory, Warehouse, Package, Cpu, Activity, GitFork,
  Search, Plus, Edit2, Trash2, RefreshCw, CheckCircle2, AlertCircle,
  X, Filter, ChevronLeft, ChevronRight, MapPin, Phone, Mail, Globe,
  Shield, Layers, Clock, ArrowRight, Wrench
} from 'lucide-react';
import {
  getCompany, updateCompany,
  listFactories, createFactory, updateFactory, deleteFactory,
  listWarehouses, createWarehouse, updateWarehouse, deleteWarehouse,
  listProducts, createProduct, updateProduct, deleteProduct,
  listComponents, createComponent, updateComponent, deleteComponent,
  listProductionLines, createProductionLine, updateProductionLine, deleteProductionLine,
  listBOMItems, createBOMItem, deleteBOMItem
} from '../services/manufacturerApi';

export default function BusinessManagement() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('company');

  // Search & Filter & Pagination states
  const [search, setSearch] = useState('');
  const [filterOption, setFilterOption] = useState('all');
  const [page, setPage] = useState(1);
  const pageSize = 8;

  // Modal states
  const [modalState, setModalState] = useState({ open: false, type: null, mode: 'create', item: null });
  const [formData, setFormData] = useState({});
  const [statusMsg, setStatusMsg] = useState(null);

  // Auto-invalidation helper for live downstream synchronization
  function refreshAllDownstreamQueries() {
    queryClient.invalidateQueries(['dashboard-overview']);
    queryClient.invalidateQueries(['dashboard-kpis']);
    queryClient.invalidateQueries(['graph-snapshot']);
    queryClient.invalidateQueries(['inventory']);
    queryClient.invalidateQueries(['reports']);
    queryClient.invalidateQueries(['recommendations']);
    queryClient.invalidateQueries(['business-company']);
    queryClient.invalidateQueries(['business-factories']);
    queryClient.invalidateQueries(['business-warehouses']);
    queryClient.invalidateQueries(['business-products']);
    queryClient.invalidateQueries(['business-components']);
    queryClient.invalidateQueries(['business-lines']);
    queryClient.invalidateQueries(['business-bom']);
  }

  // 1. Company Profile Query & Mutation
  const { data: company, isLoading: loadingCompany, refetch: refetchCompany } = useQuery({
    queryKey: ['business-company'],
    queryFn: getCompany,
  });

  const companyMutation = useMutation({
    mutationFn: (data) => updateCompany(data),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Company profile updated successfully.' });
      setModalState({ open: false });
    },
    onError: (err) => setStatusMsg({ type: 'error', text: err.message || 'Failed to update company.' })
  });

  // 2. Factories Query & Mutations
  const { data: factories = [], isLoading: loadingFactories } = useQuery({
    queryKey: ['business-factories'],
    queryFn: listFactories,
  });

  const factoryMutation = useMutation({
    mutationFn: ({ id, data, isEdit }) => isEdit ? updateFactory(id, data) : createFactory(data),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Factory saved successfully.' });
      setModalState({ open: false });
    },
    onError: (err) => setStatusMsg({ type: 'error', text: err.message || 'Factory action failed.' })
  });

  const deleteFactoryMutation = useMutation({
    mutationFn: (id) => deleteFactory(id),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Factory deleted.' });
    }
  });

  // 3. Warehouses Query & Mutations
  const { data: warehouses = [], isLoading: loadingWarehouses } = useQuery({
    queryKey: ['business-warehouses'],
    queryFn: listWarehouses,
  });

  const warehouseMutation = useMutation({
    mutationFn: ({ id, data, isEdit }) => isEdit ? updateWarehouse(id, data) : createWarehouse(data),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Warehouse saved successfully.' });
      setModalState({ open: false });
    },
    onError: (err) => setStatusMsg({ type: 'error', text: err.message || 'Warehouse action failed.' })
  });

  const deleteWarehouseMutation = useMutation({
    mutationFn: (id) => deleteWarehouse(id),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Warehouse deleted.' });
    }
  });

  // 4. Products Query & Mutations
  const { data: products = [], isLoading: loadingProducts } = useQuery({
    queryKey: ['business-products'],
    queryFn: listProducts,
  });

  const productMutation = useMutation({
    mutationFn: ({ id, data, isEdit }) => isEdit ? updateProduct(id, data) : createProduct(data),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Product saved successfully.' });
      setModalState({ open: false });
    },
    onError: (err) => setStatusMsg({ type: 'error', text: err.message || 'Product action failed.' })
  });

  const deleteProductMutation = useMutation({
    mutationFn: (id) => deleteProduct(id),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Product deleted.' });
    }
  });

  // 5. Components Query & Mutations
  const { data: components = [], isLoading: loadingComponents } = useQuery({
    queryKey: ['business-components'],
    queryFn: () => listComponents(),
  });

  const componentMutation = useMutation({
    mutationFn: ({ id, data, isEdit }) => isEdit ? updateComponent(id, data) : createComponent(data),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Component saved successfully.' });
      setModalState({ open: false });
    },
    onError: (err) => setStatusMsg({ type: 'error', text: err.message || 'Component action failed.' })
  });

  const deleteComponentMutation = useMutation({
    mutationFn: (id) => deleteComponent(id),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Component deleted.' });
    }
  });

  // 6. Production Lines Query & Mutations
  const { data: productionLines = [], isLoading: loadingLines } = useQuery({
    queryKey: ['business-lines'],
    queryFn: () => listProductionLines(),
  });

  const lineMutation = useMutation({
    mutationFn: ({ id, data, isEdit }) => isEdit ? updateProductionLine(id, data) : createProductionLine(data),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Production line saved successfully.' });
      setModalState({ open: false });
    },
    onError: (err) => setStatusMsg({ type: 'error', text: err.message || 'Production line action failed.' })
  });

  const deleteLineMutation = useMutation({
    mutationFn: (id) => deleteProductionLine(id),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'Production line deleted.' });
    }
  });

  // 7. BOM Items Query & Mutations
  const { data: bomItems = [], isLoading: loadingBOM } = useQuery({
    queryKey: ['business-bom'],
    queryFn: () => listBOMItems(),
  });

  const bomMutation = useMutation({
    mutationFn: (data) => createBOMItem(data),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'BOM linkage created.' });
      setModalState({ open: false });
    },
    onError: (err) => setStatusMsg({ type: 'error', text: err.message || 'BOM action failed.' })
  });

  const deleteBOMMutation = useMutation({
    mutationFn: (id) => deleteBOMItem(id),
    onSuccess: () => {
      refreshAllDownstreamQueries();
      setStatusMsg({ type: 'success', text: 'BOM item deleted.' });
    }
  });

  // Modal open helper
  function openModal(type, mode = 'create', item = null) {
    setModalState({ open: true, type, mode, item });
    setStatusMsg(null);
    if (mode === 'edit' && item) {
      setFormData({ ...item });
    } else {
      setFormData(
        type === 'factory' ? { factory_name: '', factory_code: '', factory_type: 'Assembly', country: 'United States', operating_status: 'Operational' } :
        type === 'warehouse' ? { warehouse_name: '', warehouse_code: '', country: 'United States', operating_status: 'Operational', temp_controlled: false } :
        type === 'product' ? { product_name: '', sku: '', category: 'Electronics', status: 'Active', production_volume: 1000 } :
        type === 'component' ? { component_name: '', category: 'Electronic', criticality: 'Medium', safety_stock: 100, unit: 'units' } :
        type === 'line' ? { factory_id: factories[0]?.id || '', line_name: '', line_code: '', capacity_per_hour: 120, operating_status: 'Operational' } :
        type === 'bom' ? { product_id: products[0]?.id || '', component_id: components[0]?.id || '', quantity_required: 1, notes: '' } :
        {}
      );
    }
  }

  // Handle modal submit
  function handleSubmit(e) {
    e.preventDefault();
    const { type, mode, item } = modalState;
    if (type === 'company') companyMutation.mutate(formData);
    if (type === 'factory') factoryMutation.mutate({ id: item?.id, data: formData, isEdit: mode === 'edit' });
    if (type === 'warehouse') warehouseMutation.mutate({ id: item?.id, data: formData, isEdit: mode === 'edit' });
    if (type === 'product') productMutation.mutate({ id: item?.id, data: formData, isEdit: mode === 'edit' });
    if (type === 'component') componentMutation.mutate({ id: item?.id, data: formData, isEdit: mode === 'edit' });
    if (type === 'line') lineMutation.mutate({ id: item?.id, data: formData, isEdit: mode === 'edit' });
    if (type === 'bom') bomMutation.mutate(formData);
  }

  // Generic filtering & pagination for active tab dataset
  const activeDataset = useMemo(() => {
    let list = [];
    if (activeTab === 'factories') list = factories;
    if (activeTab === 'warehouses') list = warehouses;
    if (activeTab === 'products') list = products;
    if (activeTab === 'components') list = components;
    if (activeTab === 'lines') list = productionLines;
    if (activeTab === 'bom') list = bomItems;

    return list.filter(item => {
      const q = search.toLowerCase();
      const matchSearch = !q || Object.values(item).some(val => val && String(val).toLowerCase().includes(q));
      let matchFilter = true;
      if (filterOption !== 'all') {
        if (item.operating_status) matchFilter = item.operating_status === filterOption;
        if (item.status) matchFilter = item.status === filterOption;
        if (item.criticality) matchFilter = item.criticality === filterOption;
      }
      return matchSearch && matchFilter;
    });
  }, [activeTab, factories, warehouses, products, components, productionLines, bomItems, search, filterOption]);

  const totalPages = Math.ceil(activeDataset.length / pageSize) || 1;
  const paginatedData = useMemo(() => {
    const start = (page - 1) * pageSize;
    return activeDataset.slice(start, start + pageSize);
  }, [activeDataset, page, pageSize]);

  return (
    <div style={{ paddingBottom: 40 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: '#111827' }}>Business Management</h1>
            <span style={{ background: '#EFF6FF', color: '#2563EB', fontSize: 12, fontWeight: 700, padding: '4px 10px', borderRadius: 12, border: '1px solid #BFDBFE' }}>
              Master Data Management (MDM)
            </span>
          </div>
          <p style={{ fontSize: 13, color: '#6B7280', marginTop: 4 }}>
            Continuous enterprise resource planning, BOM structures, facility topology, and operational metadata.
          </p>
        </div>

        <button
          onClick={refreshAllDownstreamQueries}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 8, padding: '8px 16px', fontSize: 13, fontWeight: 600, color: '#374151', cursor: 'pointer' }}
        >
          <RefreshCw size={15} /> Sync Domain Events
        </button>
      </div>

      {/* Status banner */}
      {statusMsg && (
        <div style={{
          marginBottom: 20, padding: '12px 16px', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 10,
          background: statusMsg.type === 'success' ? '#ECFDF5' : '#FEF2F2',
          border: `1px solid ${statusMsg.type === 'success' ? '#A7F3D0' : '#FCA5A5'}`,
          color: statusMsg.type === 'success' ? '#065F46' : '#991B1B',
          fontSize: 13, fontWeight: 500,
        }}>
          {statusMsg.type === 'success' ? <CheckCircle2 size={16} color="#059669" /> : <AlertCircle size={16} color="#DC2626" />}
          <span>{statusMsg.text}</span>
          <button onClick={() => setStatusMsg(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}>
            <X size={15} />
          </button>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #E5E7EB', marginBottom: 20, overflowX: 'auto', gap: 4 }}>
        {[
          { id: 'company', label: 'Company Profile', icon: Building2 },
          { id: 'factories', label: `Factories (${factories.length})`, icon: Factory },
          { id: 'warehouses', label: `Warehouses (${warehouses.length})`, icon: Warehouse },
          { id: 'products', label: `Products (${products.length})`, icon: Package },
          { id: 'components', label: `Components (${components.length})`, icon: Cpu },
          { id: 'lines', label: `Production Lines (${productionLines.length})`, icon: Activity },
          { id: 'bom', label: `BOM (${bomItems.length})`, icon: GitFork },
        ].map(tab => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setSearch(''); setFilterOption('all'); setPage(1); }}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 16px',
                border: 'none', borderBottom: active ? '2px solid #2563EB' : '2px solid transparent',
                background: 'transparent', color: active ? '#2563EB' : '#6B7280',
                fontWeight: active ? 600 : 500, fontSize: 13, cursor: 'pointer', whiteSpace: 'nowrap',
                transition: 'all 0.15s'
              }}
            >
              <Icon size={16} /> {tab.label}
            </button>
          );
        })}
      </div>

      {/* SECTION 1: COMPANY PROFILE */}
      {activeTab === 'company' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, borderBottom: '1px solid #F3F4F6', paddingBottom: 16 }}>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: '#111827' }}>Corporate Profile & Operational Metadata</h2>
              <p style={{ fontSize: 12, color: '#6B7280' }}>Primary organization identity registered in PostgreSQL database.</p>
            </div>
            <button
              onClick={() => openModal('company', 'edit', company)}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#2563EB', color: '#FFF', border: 'none', borderRadius: 6, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
            >
              <Edit2 size={14} /> Edit Profile
            </button>
          </div>

          {loadingCompany ? (
            <div style={{ padding: 40, textAlign: 'center', color: '#9CA3AF' }}>Loading company profile...</div>
          ) : company ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
              <div style={{ background: '#F9FAFB', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', marginBottom: 8 }}>Identity & Industry</div>
                <div style={{ fontSize: 18, fontWeight: 800, color: '#111827', marginBottom: 4 }}>{company.name}</div>
                <div style={{ fontSize: 13, color: '#2563EB', fontWeight: 600 }}>{company.industry}</div>
                <p style={{ fontSize: 12, color: '#4B5563', marginTop: 8, lineHeight: 1.5 }}>{company.description || 'No description provided.'}</p>
              </div>

              <div style={{ background: '#F9FAFB', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', marginBottom: 8 }}>Headquarters Location</div>
                <div style={{ fontSize: 13, color: '#374151', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <MapPin size={14} color="#6B7280" /> {company.city ? `${company.city}, ` : ''}{company.state ? `${company.state}, ` : ''}{company.country}
                </div>
                <div style={{ fontSize: 12, color: '#6B7280' }}>Address: {company.address || 'N/A'}</div>
              </div>

              <div style={{ background: '#F9FAFB', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', marginBottom: 8 }}>Corporate Contact</div>
                <div style={{ fontSize: 12, color: '#374151', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <Mail size={14} color="#6B7280" /> {company.business_email || 'N/A'}
                </div>
                <div style={{ fontSize: 12, color: '#374151', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <Phone size={14} color="#6B7280" /> {company.business_phone || 'N/A'}
                </div>
                <div style={{ fontSize: 12, color: '#374151', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Globe size={14} color="#6B7280" /> {company.website || 'N/A'}
                </div>
              </div>

              <div style={{ background: '#F9FAFB', padding: 16, borderRadius: 8, border: '1px solid #E5E7EB' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', marginBottom: 8 }}>Operating Windows</div>
                <div style={{ fontSize: 13, color: '#374151', fontWeight: 600 }}>Timezone: {company.timezone || 'UTC'}</div>
                <div style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>Hours: {company.working_hours_start} - {company.working_hours_end}</div>
              </div>
            </div>
          ) : (
            <div style={{ padding: 30, textAlign: 'center', color: '#6B7280' }}>No company details found.</div>
          )}
        </motion.div>
      )}

      {/* SECTIONS 2-7: TABULAR MDM MODULES */}
      {activeTab !== 'company' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          {/* Controls Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 260 }}>
              <div style={{ position: 'relative', flex: 1 }}>
                <Search size={15} color="#9CA3AF" style={{ position: 'absolute', left: 12, top: 10 }} />
                <input
                  type="text"
                  placeholder={`Search ${activeTab}...`}
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                  style={{ width: '100%', paddingLeft: 34, paddingRight: 12, paddingTop: 8, paddingBottom: 8, borderRadius: 6, border: '1px solid #D1D5DB', fontSize: 13 }}
                />
              </div>

              <select
                value={filterOption}
                onChange={(e) => { setFilterOption(e.target.value); setPage(1); }}
                style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #D1D5DB', fontSize: 13, background: '#FFF', color: '#374151' }}
              >
                <option value="all">All Statuses / Categories</option>
                <option value="Operational">Operational</option>
                <option value="Active">Active</option>
                <option value="High">High Criticality</option>
                <option value="Critical">Critical</option>
              </select>
            </div>

            <button
              onClick={() => openModal(activeTab.replace('factories','factory').replace('warehouses','warehouse').replace('products','product').replace('components','component').replace('lines','line'), 'create')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#2563EB', color: '#FFF', border: 'none', borderRadius: 6, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
            >
              <Plus size={16} /> Add {activeTab === 'factories' ? 'Factory' : activeTab === 'warehouses' ? 'Warehouse' : activeTab === 'products' ? 'Product' : activeTab === 'components' ? 'Component' : activeTab === 'lines' ? 'Production Line' : 'BOM Link'}
            </button>
          </div>

          {/* Table Container */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#F9FAFB', borderBottom: '1px solid #E5E7EB', color: '#6B7280', fontSize: 12, fontWeight: 700 }}>
                  {activeTab === 'factories' && (
                    <>
                      <th style={{ padding: '12px 16px' }}>Factory Name</th>
                      <th style={{ padding: '12px 16px' }}>Code</th>
                      <th style={{ padding: '12px 16px' }}>Type</th>
                      <th style={{ padding: '12px 16px' }}>Country</th>
                      <th style={{ padding: '12px 16px' }}>Status</th>
                      <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                    </>
                  )}
                  {activeTab === 'warehouses' && (
                    <>
                      <th style={{ padding: '12px 16px' }}>Warehouse Name</th>
                      <th style={{ padding: '12px 16px' }}>Code</th>
                      <th style={{ padding: '12px 16px' }}>Country</th>
                      <th style={{ padding: '12px 16px' }}>Climate Controlled</th>
                      <th style={{ padding: '12px 16px' }}>Status</th>
                      <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                    </>
                  )}
                  {activeTab === 'products' && (
                    <>
                      <th style={{ padding: '12px 16px' }}>Product Name</th>
                      <th style={{ padding: '12px 16px' }}>SKU</th>
                      <th style={{ padding: '12px 16px' }}>Category</th>
                      <th style={{ padding: '12px 16px' }}>Monthly Volume</th>
                      <th style={{ padding: '12px 16px' }}>Status</th>
                      <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                    </>
                  )}
                  {activeTab === 'components' && (
                    <>
                      <th style={{ padding: '12px 16px' }}>Component Name</th>
                      <th style={{ padding: '12px 16px' }}>Category</th>
                      <th style={{ padding: '12px 16px' }}>Criticality</th>
                      <th style={{ padding: '12px 16px' }}>Safety Stock</th>
                      <th style={{ padding: '12px 16px' }}>Preferred Supplier</th>
                      <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                    </>
                  )}
                  {activeTab === 'lines' && (
                    <>
                      <th style={{ padding: '12px 16px' }}>Line Name</th>
                      <th style={{ padding: '12px 16px' }}>Code</th>
                      <th style={{ padding: '12px 16px' }}>Factory</th>
                      <th style={{ padding: '12px 16px' }}>Cap / Hour</th>
                      <th style={{ padding: '12px 16px' }}>Status</th>
                      <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                    </>
                  )}
                  {activeTab === 'bom' && (
                    <>
                      <th style={{ padding: '12px 16px' }}>Finished Product</th>
                      <th style={{ padding: '12px 16px' }}>Component Required</th>
                      <th style={{ padding: '12px 16px' }}>Qty per Unit</th>
                      <th style={{ padding: '12px 16px' }}>Notes</th>
                      <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {paginatedData.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ padding: 40, textAlign: 'center', color: '#9CA3AF' }}>
                      No {activeTab} available. Click "Add" to create records.
                    </td>
                  </tr>
                ) : (
                  paginatedData.map((item) => (
                    <tr key={item.id} style={{ borderBottom: '1px solid #F3F4F6' }}>
                      {activeTab === 'factories' && (
                        <>
                          <td style={{ padding: '12px 16px', fontWeight: 600, color: '#111827' }}>{item.factory_name}</td>
                          <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: '#6B7280' }}>{item.factory_code}</td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.factory_type}</td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.country}</td>
                          <td style={{ padding: '12px 16px' }}>
                            <span style={{ background: '#D1FAE5', color: '#065F46', padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600 }}>{item.operating_status}</span>
                          </td>
                        </>
                      )}
                      {activeTab === 'warehouses' && (
                        <>
                          <td style={{ padding: '12px 16px', fontWeight: 600, color: '#111827' }}>{item.warehouse_name}</td>
                          <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: '#6B7280' }}>{item.warehouse_code}</td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.country}</td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.temp_controlled ? 'Yes ❄️' : 'No'}</td>
                          <td style={{ padding: '12px 16px' }}>
                            <span style={{ background: '#D1FAE5', color: '#065F46', padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600 }}>{item.operating_status}</span>
                          </td>
                        </>
                      )}
                      {activeTab === 'products' && (
                        <>
                          <td style={{ padding: '12px 16px', fontWeight: 600, color: '#111827' }}>{item.product_name}</td>
                          <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: '#6B7280' }}>{item.sku}</td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.category}</td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.production_volume?.toLocaleString() || 0}</td>
                          <td style={{ padding: '12px 16px' }}>
                            <span style={{ background: '#EFF6FF', color: '#1E40AF', padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600 }}>{item.status}</span>
                          </td>
                        </>
                      )}
                      {activeTab === 'components' && (
                        <>
                          <td style={{ padding: '12px 16px', fontWeight: 600, color: '#111827' }}>{item.component_name}</td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.category}</td>
                          <td style={{ padding: '12px 16px' }}>
                            <span style={{
                              background: item.criticality === 'Critical' ? '#FEE2E2' : item.criticality === 'High' ? '#FEF3C7' : '#EFF6FF',
                              color: item.criticality === 'Critical' ? '#991B1B' : item.criticality === 'High' ? '#92400E' : '#1E40AF',
                              padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600
                            }}>
                              {item.criticality}
                            </span>
                          </td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.safety_stock} {item.unit}</td>
                          <td style={{ padding: '12px 16px', color: '#6B7280' }}>{item.preferred_supplier || 'Unassigned'}</td>
                        </>
                      )}
                      {activeTab === 'lines' && (
                        <>
                          <td style={{ padding: '12px 16px', fontWeight: 600, color: '#111827' }}>{item.line_name}</td>
                          <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: '#6B7280' }}>{item.line_code}</td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.factory_name || 'Main Plant'}</td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.capacity_per_hour} units/hr</td>
                          <td style={{ padding: '12px 16px' }}>
                            <span style={{ background: '#D1FAE5', color: '#065F46', padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600 }}>{item.operating_status}</span>
                          </td>
                        </>
                      )}
                      {activeTab === 'bom' && (
                        <>
                          <td style={{ padding: '12px 16px', fontWeight: 600, color: '#111827' }}>{item.product_name || item.product_id}</td>
                          <td style={{ padding: '12px 16px', color: '#2563EB', fontWeight: 600 }}>{item.component_name || item.component_id}</td>
                          <td style={{ padding: '12px 16px', color: '#374151' }}>{item.quantity_required}</td>
                          <td style={{ padding: '12px 16px', color: '#6B7280' }}>{item.notes || '—'}</td>
                        </>
                      )}

                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                        {activeTab !== 'bom' && (
                          <button
                            onClick={() => openModal(activeTab.slice(0, -1), 'edit', item)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6B7280', marginRight: 10 }}
                            title="Edit"
                          >
                            <Edit2 size={15} />
                          </button>
                        )}
                        <button
                          onClick={() => {
                            if (activeTab === 'factories') deleteFactoryMutation.mutate(item.id);
                            if (activeTab === 'warehouses') deleteWarehouseMutation.mutate(item.id);
                            if (activeTab === 'products') deleteProductMutation.mutate(item.id);
                            if (activeTab === 'components') deleteComponentMutation.mutate(item.id);
                            if (activeTab === 'lines') deleteLineMutation.mutate(item.id);
                            if (activeTab === 'bom') deleteBOMMutation.mutate(item.id);
                          }}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#EF4444' }}
                          title="Delete"
                        >
                          <Trash2 size={15} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            {/* Pagination footer */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderTop: '1px solid #E5E7EB', background: '#F9FAFB', fontSize: 12, color: '#6B7280' }}>
              <div>Showing {activeDataset.length > 0 ? (page - 1) * pageSize + 1 : 0} to {Math.min(page * pageSize, activeDataset.length)} of {activeDataset.length} items</div>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <button disabled={page === 1} onClick={() => setPage(p => p - 1)} style={{ padding: '4px 8px', border: '1px solid #D1D5DB', borderRadius: 4, background: '#FFF', cursor: page === 1 ? 'not-allowed' : 'pointer' }}>
                  <ChevronLeft size={14} />
                </button>
                <span>Page {page} of {totalPages}</span>
                <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)} style={{ padding: '4px 8px', border: '1px solid #D1D5DB', borderRadius: 4, background: '#FFF', cursor: page === totalPages ? 'not-allowed' : 'pointer' }}>
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* CREATE / EDIT MODAL */}
      <AnimatePresence>
        {modalState.open && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.4)', padding: 16 }}>
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              style={{ background: '#FFFFFF', borderRadius: 12, width: '100%', maxWidth: 540, overflow: 'hidden', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}
            >
              <div style={{ padding: '16px 20px', borderBottom: '1px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#F9FAFB' }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: '#111827' }}>
                  {modalState.mode === 'edit' ? 'Edit' : 'Create New'} {modalState.type?.toUpperCase()}
                </h3>
                <button onClick={() => setModalState({ open: false })} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6B7280' }}>
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleSubmit} style={{ padding: 20 }}>
                {modalState.type === 'company' && (
                  <div style={{ display: 'grid', gap: 12 }}>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Company Name</label>
                      <input required type="text" value={formData.name || ''} onChange={e => setFormData({ ...formData, name: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Industry</label>
                      <input required type="text" value={formData.industry || ''} onChange={e => setFormData({ ...formData, industry: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Country</label>
                      <input required type="text" value={formData.country || ''} onChange={e => setFormData({ ...formData, country: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                  </div>
                )}

                {modalState.type === 'factory' && (
                  <div style={{ display: 'grid', gap: 12 }}>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Factory Name</label>
                      <input required type="text" value={formData.factory_name || ''} onChange={e => setFormData({ ...formData, factory_name: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Factory Code</label>
                      <input required type="text" value={formData.factory_code || ''} onChange={e => setFormData({ ...formData, factory_code: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Country</label>
                      <input required type="text" value={formData.country || ''} onChange={e => setFormData({ ...formData, country: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                  </div>
                )}

                {modalState.type === 'warehouse' && (
                  <div style={{ display: 'grid', gap: 12 }}>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Warehouse Name</label>
                      <input required type="text" value={formData.warehouse_name || ''} onChange={e => setFormData({ ...formData, warehouse_name: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Warehouse Code</label>
                      <input required type="text" value={formData.warehouse_code || ''} onChange={e => setFormData({ ...formData, warehouse_code: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Country</label>
                      <input required type="text" value={formData.country || ''} onChange={e => setFormData({ ...formData, country: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                  </div>
                )}

                {modalState.type === 'product' && (
                  <div style={{ display: 'grid', gap: 12 }}>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Product Name</label>
                      <input required type="text" value={formData.product_name || ''} onChange={e => setFormData({ ...formData, product_name: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>SKU</label>
                      <input required type="text" value={formData.sku || ''} onChange={e => setFormData({ ...formData, sku: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Monthly Production Volume</label>
                      <input type="number" value={formData.production_volume || 0} onChange={e => setFormData({ ...formData, production_volume: parseInt(e.target.value) || 0 })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                  </div>
                )}

                {modalState.type === 'component' && (
                  <div style={{ display: 'grid', gap: 12 }}>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Component Name</label>
                      <input required type="text" value={formData.component_name || ''} onChange={e => setFormData({ ...formData, component_name: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Criticality</label>
                      <select value={formData.criticality || 'Medium'} onChange={e => setFormData({ ...formData, criticality: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4, background: '#FFF' }}>
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                        <option value="Critical">Critical</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Safety Stock</label>
                      <input type="number" value={formData.safety_stock || 0} onChange={e => setFormData({ ...formData, safety_stock: parseInt(e.target.value) || 0 })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                  </div>
                )}

                {modalState.type === 'line' && (
                  <div style={{ display: 'grid', gap: 12 }}>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Production Line Name</label>
                      <input required type="text" value={formData.line_name || ''} onChange={e => setFormData({ ...formData, line_name: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Line Code</label>
                      <input required type="text" value={formData.line_code || ''} onChange={e => setFormData({ ...formData, line_code: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Capacity / Hour</label>
                      <input type="number" value={formData.capacity_per_hour || 100} onChange={e => setFormData({ ...formData, capacity_per_hour: parseInt(e.target.value) || 1 })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                  </div>
                )}

                {modalState.type === 'bom' && (
                  <div style={{ display: 'grid', gap: 12 }}>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Finished Product</label>
                      <select value={formData.product_id || ''} onChange={e => setFormData({ ...formData, product_id: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4, background: '#FFF' }}>
                        {products.map(p => <option key={p.id} value={p.id}>{p.product_name} ({p.sku})</option>)}
                      </select>
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Required Component</label>
                      <select value={formData.component_id || ''} onChange={e => setFormData({ ...formData, component_id: e.target.value })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4, background: '#FFF' }}>
                        {components.map(c => <option key={c.id} value={c.id}>{c.component_name}</option>)}
                      </select>
                    </div>
                    <div>
                      <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Quantity Required per Unit</label>
                      <input type="number" min="1" value={formData.quantity_required || 1} onChange={e => setFormData({ ...formData, quantity_required: parseInt(e.target.value) || 1 })} style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #D1D5DB', marginTop: 4 }} />
                    </div>
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20, paddingTop: 16, borderTop: '1px solid #E5E7EB' }}>
                  <button type="button" onClick={() => setModalState({ open: false })} style={{ padding: '8px 16px', borderRadius: 6, border: '1px solid #D1D5DB', background: '#FFF', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Cancel</button>
                  <button type="submit" style={{ padding: '8px 16px', borderRadius: 6, border: 'none', background: '#2563EB', color: '#FFF', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Save Changes</button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
