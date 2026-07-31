/**
 * setupStore.js — Zustand store for the manufacturer onboarding wizard.
 *
 * Holds in-memory state for all 7 wizard steps.
 * Auto-saves to the backend on each step completion.
 * Data persists across step navigation without re-fetching.
 */

import { create } from 'zustand';

// ── Defaults ────────────────────────────────────────────────────────────────

const DEFAULT_COMPANY = {
  name:                  '',
  industry:              'Electronics Manufacturing',
  description:           '',
  country:               '',
  state:                 '',
  city:                  '',
  address:               '',
  website:               '',
  business_email:        '',
  business_phone:        '',
  logo_url:              '',
  company_size:          '',
  annual_production_cap: '',
  registration_number:   '',
  tax_number:            '',
  timezone:              'Asia/Kolkata',
  working_days:          ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
  working_hours_start:   '09:00',
  working_hours_end:     '18:00',
};

// ── Store ────────────────────────────────────────────────────────────────────

export const useSetupStore = create((set, get) => ({
  // ── Wizard state ──────────────────────────────────────────────────────────
  currentStep:  1,
  isLoading:    false,
  isSaving:     false,
  error:        null,

  // ── Step data ─────────────────────────────────────────────────────────────
  company:    { ...DEFAULT_COMPANY },
  factories:  [],
  warehouses: [],
  products:   [],
  components: [],

  // ── Actions ───────────────────────────────────────────────────────────────

  setCurrentStep: (step) => set({ currentStep: step }),

  setLoading: (v) => set({ isLoading: v }),
  setSaving:  (v) => set({ isSaving: v }),
  setError:   (e) => set({ error: e }),

  // Company
  updateCompany: (patch) =>
    set((state) => ({ company: { ...state.company, ...patch } })),

  setCompany: (data) =>
    set({ company: { ...DEFAULT_COMPANY, ...data } }),

  // Factories
  setFactories: (list) => set({ factories: list }),

  addFactory: (factory) =>
    set((state) => ({ factories: [...state.factories, factory] })),

  updateFactory: (id, patch) =>
    set((state) => ({
      factories: state.factories.map((f) =>
        f.id === id ? { ...f, ...patch } : f,
      ),
    })),

  removeFactory: (id) =>
    set((state) => ({
      factories: state.factories.filter((f) => f.id !== id),
    })),

  // Warehouses
  setWarehouses: (list) => set({ warehouses: list }),

  addWarehouse: (wh) =>
    set((state) => ({ warehouses: [...state.warehouses, wh] })),

  updateWarehouse: (id, patch) =>
    set((state) => ({
      warehouses: state.warehouses.map((w) =>
        w.id === id ? { ...w, ...patch } : w,
      ),
    })),

  removeWarehouse: (id) =>
    set((state) => ({
      warehouses: state.warehouses.filter((w) => w.id !== id),
    })),

  // Products
  setProducts: (list) => set({ products: list }),

  addProduct: (product) =>
    set((state) => ({ products: [...state.products, product] })),

  updateProduct: (id, patch) =>
    set((state) => ({
      products: state.products.map((p) =>
        p.id === id ? { ...p, ...patch } : p,
      ),
    })),

  removeProduct: (id) =>
    set((state) => ({
      products: state.products.filter((p) => p.id !== id),
    })),

  // Components
  setComponents: (list) => set({ components: list }),

  addComponent: (comp) =>
    set((state) => ({ components: [...state.components, comp] })),

  updateComponent: (id, patch) =>
    set((state) => ({
      components: state.components.map((c) =>
        c.id === id ? { ...c, ...patch } : c,
      ),
    })),

  removeComponent: (id) =>
    set((state) => ({
      components: state.components.filter((c) => c.id !== id),
    })),

  // Reset (used on wizard completion to free memory)
  reset: () =>
    set({
      currentStep: 1,
      isLoading:   false,
      isSaving:    false,
      error:       null,
      company:     { ...DEFAULT_COMPANY },
      factories:   [],
      warehouses:  [],
      products:    [],
      components:  [],
    }),
}));
