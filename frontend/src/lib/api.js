/**
 * api.js — Centralised fetch utility + React Query client for SupplyShield AI
 *
 * All admin / manufacturer dashboard data fetching goes through this module.
 * Supabase JWT is attached automatically to every request.
 * Base URL: VITE_API_URL env var (defaults to http://localhost:8000/api/v1)
 *
 * SESSION REFRESH FIX:
 * sessionStorage sessions can expire silently (tab re-use, token TTL).
 * We now call refreshSession() if getSession() returns null before giving up,
 * which prevents the 401 on POST /manufacturer/company and similar endpoints.
 */

import { QueryClient }  from '@tanstack/react-query';
import { supabase }     from './supabase';

import { sanitizePayload } from './payloadSanitizer';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime:            30_000,   // 30 s — data considered fresh
      gcTime:              300_000,   // 5 min — keep in cache after unmount
      refetchOnWindowFocus: true,
      retry: 2,
    },
  },
});

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function getAccessToken() {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) return session.access_token;

  const { data: refreshData } = await supabase.auth.refreshSession();
  return refreshData?.session?.access_token ?? null;
}

async function request(method, path, body) {
  const token = await getAccessToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const options = { method, headers };
  if (body !== undefined) {
    const cleanBody = sanitizePayload(body);
    options.body = JSON.stringify(cleanBody);
  }

  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const msg = typeof err.detail === 'string' 
      ? err.detail 
      : Array.isArray(err.detail) 
      ? err.detail.map(d => `${d.loc?.slice(-1)[0] || 'field'}: ${d.msg}`).join(', ')
      : `${method} ${path} → ${res.status}`;
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get:    (path)        => request('GET',    path),
  post:   (path, body)  => request('POST',   path, body ?? {}),
  put:    (path, body)  => request('PUT',    path, body ?? {}),
  patch:  (path, body)  => request('PATCH',  path, body ?? {}),
  delete: (path)        => request('DELETE', path),
};
