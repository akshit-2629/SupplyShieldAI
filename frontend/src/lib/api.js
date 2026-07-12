/**
 * api.js — Centralised fetch utility + React Query client for SupplyShield AI
 *
 * All data fetching in this app goes through this module.
 * Base URL is read from VITE_API_URL env var (defaults to http://localhost:8000/api/v1).
 */

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,      // 30 s — data considered fresh
      gcTime:    300_000,     // 5 min — keep in cache after unmount
      refetchOnWindowFocus: true,
      retry: 2,
    },
  },
});

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function request(method, path, body) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) options.body = JSON.stringify(body);

  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `${method} ${path} → ${res.status}`);
  }
  // 204 No Content → return null
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get:  (path)        => request('GET',  path),
  post: (path, body)  => request('POST', path, body ?? {}),
};
