/**
 * supplierApi.js — Supplier Portal API service layer for SupplyShield AI.
 *
 * All functions make real fetch calls to the FastAPI backend.
 * Supabase JWT is attached automatically to every authenticated request.
 *
 * Base URL: VITE_API_URL env var (defaults to http://localhost:8000/api/v1)
 */

import { supabase } from '../lib/supabase';
import { sanitizePayload } from '../lib/payloadSanitizer';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const SP   = `${BASE}/supplier-portal`;

// ── Auth header helper (with session refresh fallback) ───────────────────────

async function getAccessToken() {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) return session.access_token;
  // Session expired — attempt refresh
  const { data: refreshData } = await supabase.auth.refreshSession();
  return refreshData?.session?.access_token ?? null;
}

async function authHeaders() {
  const token = await getAccessToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}


// ── Core JSON fetch wrapper ─────────────────────────────────────────────────

async function req(method, url, body) {
  const headers = await authHeaders();
  const opts    = { method, headers };
  if (body !== undefined) {
    const cleaned = sanitizePayload(body);
    opts.body = JSON.stringify(cleaned);
  }

  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    let msg = err.detail || `${method} ${url} → ${res.status}`;
    if (Array.isArray(err.detail)) {
      msg = err.detail.map(e => `${e.loc ? e.loc.join('.') : 'field'}: ${e.msg}`).join('; ');
    }
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  const json = await res.json();
  // Backend wraps all responses in { success, data, message } — unwrap
  return json.data !== undefined ? json.data : json;
}

// ── Multipart form upload (files) ───────────────────────────────────────────

async function reqForm(method, url, formData) {
  const token = await getAccessToken();
  // Do NOT set Content-Type — browser sets multipart/form-data with boundary
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(url, { method, headers, body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `${method} ${url} → ${res.status}`);
  }
  const json = await res.json();
  return json.data !== undefined ? json.data : json;
}

// ══════════════════════════════════════════════════════════════════════════════
// DASHBOARD — Aggregated parallel fetch
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Aggregates data from 7 backend endpoints in parallel.
 * Uses Promise.allSettled so one failure never blocks the dashboard.
 */
export async function getSupplierDashboard() {
  const [
    productionRes,
    productionHistoryRes,
    inventoryRes,
    shipmentsRes,
    incidentsRes,
    unreadRes,
    scoresRes,
  ] = await Promise.allSettled([
    req('GET', `${SP}/production`),
    req('GET', `${SP}/production/history`),
    req('GET', `${SP}/inventory`),
    req('GET', `${SP}/shipments?page=1&limit=200`),
    req('GET', `${SP}/incidents`),
    req('GET', `${SP}/notifications/unread`),
    req('GET', `${SP}/performance/scores`),
  ]);

  const get = (result) => (result.status === 'fulfilled' ? result.value : null);

  const production        = get(productionRes);
  const productionHistory = get(productionHistoryRes) || [];
  const inventoryItems    = get(inventoryRes)    || [];
  const rawShipments      = get(shipmentsRes);
  const incidents         = get(incidentsRes)    || [];
  const unread            = get(unreadRes);
  const scores            = get(scoresRes);

  const shipmentList = Array.isArray(rawShipments)
    ? rawShipments
    : (rawShipments?.data || rawShipments?.items || []);

  const openShipmentList = shipmentList.filter((s) => {
    const st = (s.status || '').toUpperCase();
    return st !== 'DELIVERED' && st !== 'CANCELLED';
  });

  // Derive counts
  const openShipments = openShipmentList.length > 0 ? openShipmentList.length : shipmentList.length;
  const activeIncidents = Array.isArray(incidents)
    ? incidents.filter((i) => ['ACTIVE', 'RECOVERING'].includes(i.status)).length
    : 0;
  const unreadNotifications = unread?.total_unread ?? 0;

  return {
    production,
    productionHistory: Array.isArray(productionHistory)
      ? productionHistory
      : productionHistory?.items || [],
    inventoryItems: Array.isArray(inventoryItems)
      ? inventoryItems
      : inventoryItems?.items || [],
    shipments: shipmentList,
    openShipments,
    activeIncidents,
    unreadNotifications,
    scores,
  };
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPANY PROFILE
// ══════════════════════════════════════════════════════════════════════════════

/** GET /supplier-portal/profile */
export async function getSupplierProfile() {
  return req('GET', `${SP}/profile`);
}

/** PUT /supplier-portal/profile */
export async function updateSupplierProfile(data) {
  return req('PUT', `${SP}/profile`, data);
}

/** POST /supplier-portal/profile/logo (multipart) */
export async function uploadCompanyLogo(file) {
  const fd = new FormData();
  fd.append('file', file);
  return reqForm('POST', `${SP}/profile/logo`, fd);
}

/** GET /supplier-portal/profile/documents — legacy profile docs */
export async function getProfileDocuments() {
  return req('GET', `${SP}/profile/documents`);
}

/** POST /supplier-portal/profile/documents (multipart) — legacy */
export async function uploadProfileDocument(file, docType = 'OTHER', name) {
  const fd = new FormData();
  fd.append('file', file);
  if (docType) fd.append('doc_type', docType);
  if (name)    fd.append('name', name);
  return reqForm('POST', `${SP}/profile/documents`, fd);
}

/** DELETE /supplier-portal/profile/documents/:id — legacy */
export async function deleteProfileDocument(docId) {
  return req('DELETE', `${SP}/profile/documents/${docId}`);
}

// Legacy aliases kept for backwards compat with existing page imports
export const getCertifications   = getProfileDocuments;
export const addCertification    = (data) => req('POST', `${SP}/profile/documents`, data);
export const deleteCertification = (id)   => deleteProfileDocument(id);

// ══════════════════════════════════════════════════════════════════════════════
// PRODUCTION CAPACITY
// ══════════════════════════════════════════════════════════════════════════════

/** GET /supplier-portal/production — latest snapshot */
export async function getProductionCapacity() {
  return req('GET', `${SP}/production`);
}

/** POST /supplier-portal/production — submit update, triggers orchestrator */
export async function updateProductionCapacity(data) {
  return req('POST', `${SP}/production`, data);
}

/** GET /supplier-portal/production/history — paginated history */
export async function getProductionCalendar() {
  return req('GET', `${SP}/production/history`);
}

export const updateProductionCalendar = updateProductionCapacity;
// Alias for SupplierSetup.jsx compatibility
export const submitProductionUpdate   = updateProductionCapacity;


// ══════════════════════════════════════════════════════════════════════════════
// INVENTORY
// ══════════════════════════════════════════════════════════════════════════════

/** GET /supplier-portal/inventory */
export async function getInventory(category) {
  const params = category && category !== 'all' ? `?category=${category}` : '';
  return req('GET', `${SP}/inventory${params}`);
}

/** POST /supplier-portal/inventory */
export async function createInventoryItem(data) {
  return req('POST', `${SP}/inventory`, data);
}

/** PUT /supplier-portal/inventory/:id — triggers orchestrator */
export async function updateInventoryItem(id, data) {
  return req('PUT', `${SP}/inventory/${id}`, data);
}

/** DELETE /supplier-portal/inventory/:id (soft delete) */
export async function deleteInventoryItem(id) {
  return req('DELETE', `${SP}/inventory/${id}`);
}

/** GET /supplier-portal/inventory (paginated) */
export async function getInventoryHistory() {
  return req('GET', `${SP}/inventory?page=1&limit=200`);
}

/** GET /supplier-portal/inventory/low-stock */
export async function getLowStockItems() {
  return req('GET', `${SP}/inventory/low-stock`);
}

/** GET /supplier-portal/inventory/critical */
export async function getCriticalItems() {
  return req('GET', `${SP}/inventory/critical`);
}

// ══════════════════════════════════════════════════════════════════════════════
// LEAD TIMES
// ══════════════════════════════════════════════════════════════════════════════

/** GET /supplier-portal/lead-times */
export async function getLeadTimes() {
  return req('GET', `${SP}/lead-times`);
}

/** POST /supplier-portal/lead-times */
export async function updateLeadTime(data) {
  return req('POST', `${SP}/lead-times`, data);
}
// Alias for SupplierSetup.jsx compatibility
export const createLeadTime = updateLeadTime;

/** GET /supplier-portal/lead-times/trends */
export async function getLeadTimeHistory() {
  return req('GET', `${SP}/lead-times/trends`);
}


// ══════════════════════════════════════════════════════════════════════════════
// SHIPMENTS
// ══════════════════════════════════════════════════════════════════════════════

/** GET /supplier-portal/shipments — supports params object or page/limit positional args */
export async function getShipments(pageOrParams = 1, limit = 20) {
  if (typeof pageOrParams === 'object') {
    const qs = new URLSearchParams(Object.fromEntries(Object.entries(pageOrParams).filter(([, v]) => v != null && v !== '')));
    return req('GET', `${SP}/shipments${qs.toString() ? '?' + qs : ''}`);
  }
  return req('GET', `${SP}/shipments?page=${pageOrParams}&limit=${limit}`);
}

/** GET /supplier-portal/shipments/:id */
export async function getShipmentById(id) {
  return req('GET', `${SP}/shipments/${id}`);
}

/** POST /supplier-portal/shipments */
export async function createShipment(data) {
  return req('POST', `${SP}/shipments`, data);
}

/** PUT /supplier-portal/shipments/:id */
export async function updateShipment(id, data) {
  return req('PUT', `${SP}/shipments/${id}`, data);
}

/** PUT /supplier-portal/shipments/:id/status */
export async function updateShipmentStatus(id, status, notes) {
  return req('PUT', `${SP}/shipments/${id}/status`, { status, notes });
}

/** GET /supplier-portal/shipments/:id/tracking */
export async function getShipmentTracking(id) {
  return req('GET', `${SP}/shipments/${id}/tracking`);
}

/** DELETE /supplier-portal/shipments/:id */
export async function deleteShipment(id) {
  return req('DELETE', `${SP}/shipments/${id}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// INCIDENTS
// ══════════════════════════════════════════════════════════════════════════════

/** GET /supplier-portal/incidents — supports optional params object */
export async function getIncidents(params) {
  if (params && typeof params === 'object') {
    const qs = new URLSearchParams(Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== '')));
    return req('GET', `${SP}/incidents${qs.toString() ? '?' + qs : ''}`);
  }
  return req('GET', `${SP}/incidents`);
}

/** POST /supplier-portal/incidents — triggers AI agents */
export async function createIncident(data) {
  return req('POST', `${SP}/incidents`, data);
}

/** PUT /supplier-portal/incidents/:id */
export async function updateIncident(id, data) {
  return req('PUT', `${SP}/incidents/${id}`, data);
}

/** POST /supplier-portal/incidents/:id/attachments (multipart) */
export async function uploadIncidentAttachment(incidentId, file) {
  const fd = new FormData();
  fd.append('file', file);
  return reqForm('POST', `${SP}/incidents/${incidentId}/attachments`, fd);
}

// ══════════════════════════════════════════════════════════════════════════════
// CAPACITY FORECAST
// ══════════════════════════════════════════════════════════════════════════════

/** GET /supplier-portal/forecasts/monthly/:year or /quarterly/:year */
export async function getForecast(period = 'monthly', year = new Date().getFullYear()) {
  const path = period === 'quarterly'
    ? `${SP}/forecasts/quarterly/${year}`
    : `${SP}/forecasts/monthly/${year}`;
  return req('GET', path);
}

/** POST /supplier-portal/forecasts — triggers orchestrator */
export async function submitForecast(data) {
  return req('POST', `${SP}/forecasts`, data);
}

/** GET /supplier-portal/forecasts/history */
export async function getForecastHistory() {
  return req('GET', `${SP}/forecasts/history`);
}

// ══════════════════════════════════════════════════════════════════════════════
// AI PERFORMANCE METRICS
// ══════════════════════════════════════════════════════════════════════════════

/** GET /supplier-portal/performance/scores — read-only, AI-generated */
export async function getPerformanceMetrics() {
  return req('GET', `${SP}/performance/scores`);
}

/** GET /supplier-portal/performance/history */
export async function getMetricsHistory() {
  return req('GET', `${SP}/performance/history`);
}

// ══════════════════════════════════════════════════════════════════════════════
// NOTIFICATIONS
// ══════════════════════════════════════════════════════════════════════════════

/** GET /supplier-portal/notifications */
export async function getNotifications(category = 'all') {
  const params = category && category !== 'all' ? `?category=${category}` : '';
  return req('GET', `${SP}/notifications${params}`);
}

/** GET /supplier-portal/notifications/unread — count by category */
export async function getUnreadCount() {
  return req('GET', `${SP}/notifications/unread`);
}

/** POST /supplier-portal/notifications/:id/read */
export async function markNotificationRead(id) {
  return req('POST', `${SP}/notifications/${id}/read`);
}

/** POST /supplier-portal/notifications/read-all */
export async function markAllNotificationsRead() {
  return req('POST', `${SP}/notifications/read-all`);
}

/** DELETE /supplier-portal/notifications/:id */
export async function deleteNotification(id) {
  return req('DELETE', `${SP}/notifications/${id}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// SUPPORT
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Returns static FAQs (no dedicated backend endpoint).
 * These answers are product-level and don't change per supplier.
 */
export async function getFaqs() {
  return [
    {
      id: 1,
      q: 'How do I update my production capacity?',
      a: 'Navigate to Production Capacity and submit a new capacity update. It automatically triggers the SupplyShield AI orchestrator which runs the Supplier Intelligence and Knowledge Graph agents.',
    },
    {
      id: 2,
      q: 'How long does account approval take?',
      a: 'Account approvals are typically reviewed within 1–2 business days. You will receive an email notification once your account is approved or if additional information is required.',
    },
    {
      id: 3,
      q: 'What happens when I report an incident?',
      a: 'Reporting an incident triggers the MasterOrchestrator which runs Risk Assessment, Knowledge Graph, and Recommendation agents automatically, updating the Executive Dashboard in real time.',
    },
    {
      id: 4,
      q: 'How are AI performance scores calculated?',
      a: 'Scores are generated by the Supplier Intelligence Agent using your submitted capacity, inventory, lead time, and historical data combined with real-time risk assessments. They update after each workflow run.',
    },
    {
      id: 5,
      q: 'Can I update my inventory in bulk?',
      a: 'Yes — use the Bulk Update feature in Inventory Management to update multiple items simultaneously.',
    },
    {
      id: 6,
      q: 'How do I track a shipment?',
      a: 'Go to Shipment Management, find the shipment, and click "View Tracking" to see the full carrier event timeline.',
    },
    {
      id: 7,
      q: 'Why is my dashboard showing dashes instead of data?',
      a: 'Dashes appear when no data has been submitted yet. Complete your Company Profile, submit a Production Capacity update, and add inventory items to populate the dashboard.',
    },
  ];
}

/** GET /supplier-portal/support/tickets */
export async function getSupportTickets() {
  return req('GET', `${SP}/support/tickets`);
}

/** POST /supplier-portal/support/tickets */
export async function createSupportTicket(data) {
  return req('POST', `${SP}/support/tickets`, data);
}

// ══════════════════════════════════════════════════════════════════════════════
// SETTINGS
// ══════════════════════════════════════════════════════════════════════════════

/** GET /supplier-portal/settings/profile */
export async function getSupplierSettings() {
  return req('GET', `${SP}/settings/profile`);
}

/** PUT /supplier-portal/settings/profile */
export async function updateSupplierSettings(data) {
  return req('PUT', `${SP}/settings/profile`, data);
}

/** GET /supplier-portal/settings/sessions */
export async function getActiveSessions() {
  return req('GET', `${SP}/settings/sessions`);
}

/** DELETE /supplier-portal/settings/sessions/:id */
export async function revokeSession(id) {
  return req('DELETE', `${SP}/settings/sessions/${id}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// MODULE C — SETUP STATUS
// ══════════════════════════════════════════════════════════════════════════════
export async function getSetupStatus() { return req('GET', `${SP}/setup-status`); }
export async function markSetupStep(step) { return req('POST', `${SP}/setup-status/step/${step}`); }
export async function markSetupComplete() { return req('POST', `${SP}/setup-status/complete`); }

// ══════════════════════════════════════════════════════════════════════════════
// MODULE C — QUALITY MANAGEMENT
// ══════════════════════════════════════════════════════════════════════════════
export async function getQualityRecords(params = {}) {
  const qs = new URLSearchParams(Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== '')));
  return req('GET', `${SP}/quality${qs.toString() ? '?' + qs : ''}`);
}
export async function getQualityKpis() { return req('GET', `${SP}/quality/kpis`); }
export async function createQualityRecord(data) { return req('POST', `${SP}/quality`, data); }
export async function getQualityRecord(id) { return req('GET', `${SP}/quality/${id}`); }
export async function updateQualityRecord(id, data) { return req('PUT', `${SP}/quality/${id}`, data); }
export async function deleteQualityRecord(id) { return req('DELETE', `${SP}/quality/${id}`); }
export async function getQualityHistory(id) { return req('GET', `${SP}/quality/${id}/history`); }

// ══════════════════════════════════════════════════════════════════════════════
// MODULE C — DOCUMENT CENTER
// ══════════════════════════════════════════════════════════════════════════════
export async function getDocuments(params = {}) {
  const qs = new URLSearchParams(Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== '')));
  return req('GET', `${SP}/documents${qs.toString() ? '?' + qs : ''}`);
}
export async function getExpiringDocuments(days = 30) { return req('GET', `${SP}/documents/expiring?days=${days}`); }
export async function uploadDocument(file, meta = {}) {
  const { supabase } = await import('../lib/supabase');
  const { data: { session } } = await supabase.auth.getSession();
  const fd = new FormData();
  fd.append('file', file);
  Object.entries(meta).forEach(([k, v]) => { if (v != null) fd.append(k, String(v)); });
  const headers = {};
  if (session?.access_token) headers['Authorization'] = `Bearer ${session.access_token}`;
  const res = await fetch(`${SP}/documents`, { method: 'POST', headers, body: fd });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(err.detail || `Upload failed: ${res.status}`); }
  const json = await res.json();
  return json.data !== undefined ? json.data : json;
}
export async function getDocument(id) { return req('GET', `${SP}/documents/${id}`); }
export async function updateDocument(id, data) { return req('PUT', `${SP}/documents/${id}`, data); }
export async function deleteDocument(id) { return req('DELETE', `${SP}/documents/${id}`); }
export async function getDocumentVersions(id) { return req('GET', `${SP}/documents/${id}/versions`); }
export async function getDocumentAudit(id) { return req('GET', `${SP}/documents/${id}/audit`); }


// =============================================================================
// MODULE C — INVENTORY DATA LOAD HELPERS
// (markNotificationRead, markAllNotificationsRead — defined above ~line 359)
// (getShipments — defined above ~line 251, supports params object)
// (getIncidents — defined above ~line 289, supports params object)
// =============================================================================
export async function getInventoryItems(params = {}) {
  const qs = new URLSearchParams(Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== "")));
  return req("GET", `${SP}/inventory${qs.toString() ? "?" + qs : ""}`);
}
export async function getWarehouseSummary() {
  return req("GET", `${SP}/inventory/warehouse-summary`);
}
