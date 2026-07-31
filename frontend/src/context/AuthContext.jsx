import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';

const AuthContext = createContext({
  user: null,
  session: null,
  loading: true,
  signOut: async () => {},
});

/**
 * AuthProvider — Manufacturer / Admin portal auth context.
 *
 * ROLE ISOLATION: This context ONLY accepts sessions where
 *   role !== 'supplier'
 * If a supplier is logged in, this context treats them as unauthenticated
 * so they cannot access manufacturer-only routes.
 *
 * Relies on Supabase onAuthStateChange to stay in sync across tabs/redirects.
 */
export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  function syncFromSession(session) {
    const u = session?.user ?? null;
    // Role isolation: suppliers must not bleed into manufacturer context
    const role = u?.user_metadata?.role;
    if (role === 'supplier') {
      // Supplier session — this context ignores it
      setUser(null);
      setSession(null);
    } else {
      setUser(u);
      setSession(session ?? null);
    }
    setLoading(false);
  }

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      syncFromSession(session);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => syncFromSession(session)
    );

    return () => subscription.unsubscribe();
  }, []);

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
};
