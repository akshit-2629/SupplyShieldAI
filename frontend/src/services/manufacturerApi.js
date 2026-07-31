/**
 * manufacturerApi.js — Authenticated API calls for the manufacturer onboarding wizard.
 * All calls target /api/v1/manufacturer/...
 * JWT from Supabase auth is attached on every request.
 */

import { supabase } from '../lib/supabase';

const BASE = `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/manufacturer`;

// ── Auth header helper (with session refresh fallback) ───────────────────────
// sessionStorage sessions can expire silently. We try refreshSession()
// before giving up so the Bearer token is never silently absent.

async function getAccessToken() {
  // supabase.auth.getSession() in JS v2 automatically refreshes
  // the access token if it's expired (using the stored refresh token).
  // We call it directly — no manual refreshSession() needed.
  const { data: { session }, error } = await supabase.auth.getSession();

  if (error) {
    console.warn('[manufacturerApi] getSession error:', error.message);
  }

  if (session?.access_token) {
    // Sanity check: verify the token isn't expired locally
    // (Supabase should handle this, but belt-and-suspenders)
    try {
      const [, payloadB64] = session.access_token.split('.');
      const payload = JSON.parse(atob(payloadB64 + '=='.slice((payloadB64.length + 3) % 4)));
      const exp = payload.exp * 1000;
      if (Date.now() < exp - 10_000) {
        // Token valid for at least 10 more seconds
        console.debug('[manufacturerApi] Token valid, expires in', Math.round((exp - Date.now()) / 1000), 'sec');
        return session.access_token;
      }
      // Token expiring very soon or expired — force a refresh
      console.debug('[manufacturerApi] Token near/past expiry, forcing refresh...');
    } catch (_) {
      // Can't decode token locally — send it anyway, let backend decide
      return session.access_token;
    }
  }

  // No session or token expired — attempt a refresh
  console.debug('[manufacturerApi] Attempting refreshSession...');
  const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession();
  if (refreshError) {
    console.warn('[manufacturerApi] refreshSession error:', refreshError.message);
  }
  if (refreshData?.session?.access_token) {
    console.debug('[manufacturerApi] Token refreshed successfully.');
    return refreshData.session.access_token;
  }

  console.warn('[manufacturerApi] No valid session — user must re-login.');
  return null;
}

async function authHeaders() {
  const token = await getAccessToken();
  const h = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}


// ── Core fetch wrapper ──────────────────────────────────────────────────────

async function req(method, url, body) {
  const headers = await authHeaders();
  const opts    = { method, headers };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    const msg = err.message || err.detail || `${method} ${url} → ${res.status}`;
    console.error('[manufacturerApi] API error', res.status, msg);
    // Special case: 401 means session truly expired — sign out and redirect
    if (res.status === 401) {
      console.warn('[manufacturerApi] 401 received — clearing session, redirecting to login');
      await supabase.auth.signOut();
      window.location.href = '/login?error=session_expired';
      return;
    }
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ══════════════════════════════════════════════════════════════════════════════
// SETUP STATUS — called by ProtectedRoute on every dashboard navigation
// ══════════════════════════════════════════════════════════════════════════════

/** @returns {{ complete: boolean, current_step: number, company_exists: boolean }} */
export async function getSetupStatus() {
  return req('GET', `${BASE}/setup-status`);
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPANY — Step 1
// ══════════════════════════════════════════════════════════════════════════════

export async function getCompany() {
  return req('GET', `${BASE}/company`).catch(e => {
    if (e.message.includes('404')) return null;
    throw e;
  });
}

/** @param {Object} data - CompanyCreate payload */
export async function upsertCompany(data) {
  return req('POST', `${BASE}/company`, data);
}

export async function updateCompany(data) {
  return req('PUT', `${BASE}/company`, data);
}

// ══════════════════════════════════════════════════════════════════════════════
// FACTORIES — Step 2
// ══════════════════════════════════════════════════════════════════════════════

export async function listFactories() {
  return req('GET', `${BASE}/factories`);
}

export async function createFactory(data) {
  return req('POST', `${BASE}/factories`, data);
}

export async function updateFactory(id, data) {
  return req('PUT', `${BASE}/factories/${id}`, data);
}

export async function deleteFactory(id) {
  return req('DELETE', `${BASE}/factories/${id}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// WAREHOUSES — Step 3
// ══════════════════════════════════════════════════════════════════════════════

export async function listWarehouses() {
  return req('GET', `${BASE}/warehouses`);
}

export async function createWarehouse(data) {
  return req('POST', `${BASE}/warehouses`, data);
}

export async function updateWarehouse(id, data) {
  return req('PUT', `${BASE}/warehouses/${id}`, data);
}

export async function deleteWarehouse(id) {
  return req('DELETE', `${BASE}/warehouses/${id}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// PRODUCTS — Step 4
// ══════════════════════════════════════════════════════════════════════════════

export async function listProducts() {
  return req('GET', `${BASE}/products`);
}

export async function createProduct(data) {
  return req('POST', `${BASE}/products`, data);
}

export async function updateProduct(id, data) {
  return req('PUT', `${BASE}/products/${id}`, data);
}

export async function deleteProduct(id) {
  return req('DELETE', `${BASE}/products/${id}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPONENTS — Step 5
// ══════════════════════════════════════════════════════════════════════════════

export async function listComponents(productId) {
  const q = productId ? `?product_id=${productId}` : '';
  return req('GET', `${BASE}/components${q}`);
}

export async function createComponent(data) {
  return req('POST', `${BASE}/components`, data);
}

export async function updateComponent(id, data) {
  return req('PUT', `${BASE}/components/${id}`, data);
}

export async function deleteComponent(id) {
  return req('DELETE', `${BASE}/components/${id}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// PRODUCTION LINES — MDM Module
// ══════════════════════════════════════════════════════════════════════════════

export async function listProductionLines(factoryId) {
  const q = factoryId ? `?factory_id=${factoryId}` : '';
  return req('GET', `${BASE}/production-lines${q}`);
}

export async function createProductionLine(data) {
  return req('POST', `${BASE}/production-lines`, data);
}

export async function updateProductionLine(id, data) {
  return req('PUT', `${BASE}/production-lines/${id}`, data);
}

export async function deleteProductionLine(id) {
  return req('DELETE', `${BASE}/production-lines/${id}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// BILLS OF MATERIALS (BOM) — MDM Module
// ══════════════════════════════════════════════════════════════════════════════

export async function listBOMItems(productId) {
  const q = productId ? `?product_id=${productId}` : '';
  return req('GET', `${BASE}/bom${q}`);
}

export async function createBOMItem(data) {
  return req('POST', `${BASE}/bom`, data);
}

export async function deleteBOMItem(id) {
  return req('DELETE', `${BASE}/bom/${id}`);
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPLETE SETUP — Step 7
// ══════════════════════════════════════════════════════════════════════════════

export async function completeSetup() {
  return req('POST', `${BASE}/complete-setup`);
}
