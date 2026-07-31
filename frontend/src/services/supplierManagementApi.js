/**
 * supplierManagementApi.js — All manufacturer-side Supplier Lifecycle Management API calls.
 *
 * Every function uses the Supabase JWT from the manufacturer's auth session.
 * Base URL: /api/v1
 */

import { supabase } from '../lib/supabase';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';



// ── Auth helper ───────────────────────────────────────────────────────────────

async function authHeaders() {
  const { data } = await supabase.auth.getSession();
  const token = data?.session?.access_token;
  if (!token) throw new Error('Not authenticated');
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
}

async function request(path, options = {}) {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}${path}`, { ...options, headers: { ...headers, ...options.headers } });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const j = await res.json(); msg = j.detail || j.message || msg; } catch (_) {}
    throw new Error(msg);
  }
  return res.json();
}

// ── Public (no auth) ──────────────────────────────────────────────────────────

/**
 * Validate an invitation token before the supplier registration form loads.
 * No auth header needed.
 */
export async function validateInvitationToken(token) {
  const res = await fetch(`${BASE}/supplier-invitations/validate?token=${token}`);
  if (!res.ok) return { valid: false, error: `HTTP ${res.status}` };
  return res.json();
}

// ── Invitations ───────────────────────────────────────────────────────────────

export async function sendInvitation(data) {
  return request('/supplier-management/invitations', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function listInvitations({ status, page = 1, pageSize = 20 } = {}) {
  const params = new URLSearchParams({ page, page_size: pageSize });
  if (status) params.set('status', status);
  return request(`/supplier-management/invitations?${params}`);
}

export async function resendInvitation(invitationId) {
  return request(`/supplier-management/invitations/${invitationId}/resend`, { method: 'POST' });
}

export async function cancelInvitation(invitationId) {
  return request(`/supplier-management/invitations/${invitationId}`, { method: 'DELETE' });
}

// ── Supplier Directory ────────────────────────────────────────────────────────

export async function listSuppliers({
  status,
  search,
  country,
  riskRating,
  isCritical,
  sortBy = 'created_at',
  sortDir = 'desc',
  page = 1,
  pageSize = 20,
} = {}) {
  const params = new URLSearchParams({ sort_by: sortBy, sort_dir: sortDir, page, page_size: pageSize });
  if (status)     params.set('status', status);
  if (search)     params.set('search', search);
  if (country)    params.set('country', country);
  if (riskRating) params.set('risk_rating', riskRating);
  if (isCritical !== undefined) params.set('is_critical', isCritical);
  return request(`/supplier-management/suppliers?${params}`);
}

export async function getSupplier(supplierUid) {
  return request(`/supplier-management/suppliers/${supplierUid}`);
}

// ── Approval Actions ──────────────────────────────────────────────────────────

export async function approveSupplier(supplierUid, note = '') {
  return request(`/supplier-management/suppliers/${supplierUid}/approve`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  });
}

export async function rejectSupplier(supplierUid, reason) {
  return request(`/supplier-management/suppliers/${supplierUid}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function suspendSupplier(supplierUid, reason) {
  return request(`/supplier-management/suppliers/${supplierUid}/suspend`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function reactivateSupplier(supplierUid) {
  return request(`/supplier-management/suppliers/${supplierUid}/reactivate`, { method: 'POST' });
}

// ── Notes ─────────────────────────────────────────────────────────────────────

export async function addNote(supplierUid, noteType, content) {
  return request(`/supplier-management/suppliers/${supplierUid}/notes`, {
    method: 'POST',
    body: JSON.stringify({ note_type: noteType, content }),
  });
}

export async function listNotes(supplierUid) {
  return request(`/supplier-management/suppliers/${supplierUid}/notes`);
}

// ── Audit ─────────────────────────────────────────────────────────────────────

export async function getAuditLog(supplierUid, limit = 50) {
  return request(`/supplier-management/suppliers/${supplierUid}/audit?limit=${limit}`);
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export async function getSupplierAnalytics() {
  return request('/supplier-management/analytics');
}

// ── Export ────────────────────────────────────────────────────────────────────

export async function exportSuppliersCSV() {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}/supplier-management/export`, { headers });
  if (!res.ok) throw new Error(`Export failed: HTTP ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `suppliers_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
