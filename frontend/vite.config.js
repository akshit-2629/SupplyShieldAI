import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],

  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {


    // Raise the advisory threshold — individual split chunks can be >200 kB without warning
    chunkSizeWarningLimit: 600,

    rollupOptions: {
      output: {
        /**
         * manualChunks — production code-splitting strategy.
         *
         * The function receives a module ID (file path) and returns the name
         * of the chunk it should be placed in. Returning undefined lets the
         * bundler decide automatically (page-level code-splitting still works).
         *
         * Grouping strategy:
         *   react-core    — React, ReactDOM, React Router (always loaded first)
         *   recharts      — Recharts + its D3 sub-packages (~400 kB raw)
         *   leaflet       — Leaflet + React-Leaflet map libraries (~150 kB raw)
         *   xyflow        — @xyflow/react knowledge-graph renderer (~180 kB raw)
         *   supabase      — Supabase JS client (~100 kB raw)
         *   tanstack      — React Query + React Table (~80 kB raw)
         *   framer        — Framer Motion animation engine (~140 kB raw)
         *   lucide        — Lucide icon set (~50 kB raw)
         *   vendor        — All remaining third-party libs (zustand, zod, etc.)
         */
        manualChunks(id) {
          // ── React ecosystem ──────────────────────────────────────────────
          if (
            id.includes('/node_modules/react/') ||
            id.includes('/node_modules/react-dom/') ||
            id.includes('/node_modules/react-router') ||
            id.includes('/node_modules/@remix-run/')
          ) {
            return 'react-core';
          }

          // ── Recharts + D3 primitives it bundles internally ──────────────
          if (
            id.includes('/node_modules/recharts') ||
            id.includes('/node_modules/d3-') ||
            id.includes('/node_modules/victory-vendor') ||
            id.includes('/node_modules/eventemitter3')
          ) {
            return 'recharts';
          }

          // ── Leaflet / React-Leaflet ──────────────────────────────────────
          if (
            id.includes('/node_modules/leaflet') ||
            id.includes('/node_modules/react-leaflet') ||
            id.includes('/node_modules/@react-leaflet')
          ) {
            return 'leaflet';
          }

          // ── @xyflow/react (Knowledge Graph) ──────────────────────────────
          if (
            id.includes('/node_modules/@xyflow') ||
            id.includes('/node_modules/reactflow')
          ) {
            return 'xyflow';
          }

          // ── Supabase client ───────────────────────────────────────────────
          if (id.includes('/node_modules/@supabase')) {
            return 'supabase';
          }

          // ── TanStack (React Query + React Table) ─────────────────────────
          if (id.includes('/node_modules/@tanstack')) {
            return 'tanstack';
          }

          // ── Framer Motion ─────────────────────────────────────────────────
          if (id.includes('/node_modules/framer-motion')) {
            return 'framer';
          }

          // ── Lucide icons ──────────────────────────────────────────────────
          if (id.includes('/node_modules/lucide-react')) {
            return 'lucide';
          }

          // ── All remaining third-party libraries ───────────────────────────
          // (zustand, zod, clsx, date-fns, sonner, react-hot-toast, etc.)
          if (id.includes('/node_modules/')) {
            return 'vendor';
          }

          // App code → let Vite split by route automatically (undefined)
        },
      },
    },
  },
})
