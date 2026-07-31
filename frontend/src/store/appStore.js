import { create } from 'zustand';

export const useAppStore = create((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  commandPaletteOpen: false,
  setCommandPaletteOpen: (v) => set({ commandPaletteOpen: v }),

  notifications: 0,
  clearNotifications: () => set({ notifications: 0 }),

  activeWorkflow: false,
  setActiveWorkflow: (v) => set({ activeWorkflow: v }),
}));
