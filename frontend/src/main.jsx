import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './lib/api.js'
import { isMissingSupabaseConfig } from './lib/supabase.js'

// ── Guard: show a helpful error page instead of a blank white screen
// when Supabase env vars are not configured (e.g. fresh Vercel deploy).
if (isMissingSupabaseConfig) {
  document.getElementById('root').innerHTML = `
    <div style="min-height:100vh;background:#0f172a;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px;font-family:system-ui,sans-serif;text-align:center;">
      <div style="background:#1e293b;border:1px solid #f87171;border-radius:16px;padding:40px 48px;max-width:540px;width:100%;">
        <div style="font-size:40px;margin-bottom:16px;">⚙️</div>
        <h1 style="font-size:22px;font-weight:700;color:#f8fafc;margin:0 0 12px;">Configuration Required</h1>
        <p style="font-size:14px;color:#94a3b8;line-height:1.7;margin:0 0 24px;">
          SupplyShield AI is missing its Supabase credentials.<br/>
          Add the following environment variables in your <strong style="color:#f8fafc">Vercel project settings</strong>, then redeploy.
        </p>
        <div style="background:#0f172a;border:1px solid #334155;border-radius:8px;padding:16px;text-align:left;font-family:monospace;font-size:13px;color:#7dd3fc;line-height:2;">
          VITE_SUPABASE_URL<br/>
          VITE_SUPABASE_ANON_KEY<br/>
          VITE_API_URL
        </div>
        <p style="font-size:12px;color:#475569;margin:20px 0 0;">
          Vercel → Project → Settings → Environment Variables
        </p>
      </div>
    </div>
  `;
} else {
  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </StrictMode>,
  )
}

