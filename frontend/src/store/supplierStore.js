import { create } from 'zustand';

/**
 * supplierStore — Zustand store for supplier portal state.
 * Keeps UI state (sidebar, notifications, drafts) separate from app-wide state.
 */
export const useSupplierStore = create((set) => ({
  // Sidebar
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (v) => set({ sidebarOpen: v }),

  // Notification badge count (populated after API call)
  unreadCount: 0,
  setUnreadCount: (n) => set({ unreadCount: n }),
  decrementUnread: () => set((s) => ({ unreadCount: Math.max(0, s.unreadCount - 1) })),
  clearUnread: () => set({ unreadCount: 0 }),

  // Form draft persistence (keyed by module)
  drafts: {},
  saveDraft: (module, data) => set((s) => ({ drafts: { ...s.drafts, [module]: data } })),
  clearDraft: (module) => set((s) => {
    const d = { ...s.drafts };
    delete d[module];
    return { drafts: d };
  }),

  // Global portal search query
  searchQuery: '',
  setSearchQuery: (q) => set({ searchQuery: q }),

  // Active notification panel
  notificationPanelOpen: false,
  toggleNotificationPanel: () => set((s) => ({ notificationPanelOpen: !s.notificationPanelOpen })),
}));
