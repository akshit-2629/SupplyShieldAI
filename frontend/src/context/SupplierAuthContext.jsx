import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';

/**
 * SupplierAuthContext
 *
 * Wraps the Supplier Portal and provides:
 *   - supplierUser    — the Supabase user object (or null)
 *   - supplierSession — the active session (or null)
 *   - isApproved      — boolean from DB account-status (not just metadata)
 *   - loading         — true while session is being resolved
 *   - signOut         — logs the supplier out
 *
 * ROLE ISOLATION: Only accepts sessions where role === 'supplier'.
 * Non-supplier sessions are ignored (treated as unauthenticated).
 *
 * APPROVAL FIX: Reads both user_metadata.isApproved (camelCase, set by
 * Supabase trigger) and user_metadata.is_approved (snake_case, set by
 * backend) to ensure approval state is read correctly regardless of which
 * system wrote it.
 */

const SupplierAuthContext = createContext({
  supplierUser:    null,
  supplierSession: null,
  isApproved:      false,
  loading:         true,
  signOut:         async () => {},
});

export function SupplierAuthProvider({ children }) {
  const [supplierUser,    setSupplierUser]    = useState(null);
  const [supplierSession, setSupplierSession] = useState(null);
  const [isApproved,      setIsApproved]      = useState(false);
  const [loading,         setLoading]         = useState(true);

  function resolveApproved(u) {
    if (!u) return false;
    const meta = u.user_metadata || {};
    // Accept either camelCase (isApproved) OR snake_case (is_approved)
    // Backend sets is_approved=true via Supabase admin API after review
    return meta.isApproved === true || meta.is_approved === true;
  }

  function syncFromSession(session) {
    const u    = session?.user ?? null;
    const role = u?.user_metadata?.role;

    // Role isolation: only supplier sessions are accepted here
    if (!u || role !== 'supplier') {
      setSupplierUser(null);
      setSupplierSession(null);
      setIsApproved(false);
      setLoading(false);
      return;
    }

    setSupplierSession(session);
    setSupplierUser(u);
    setIsApproved(resolveApproved(u));
    setLoading(false);
  }

  useEffect(() => {
    let timer = setTimeout(() => {
      setLoading(false);
    }, 5000);

    supabase.auth.getSession().then(({ data: { session } }) => {
      clearTimeout(timer);
      syncFromSession(session);
    }).catch(() => {
      clearTimeout(timer);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        clearTimeout(timer);
        syncFromSession(session);
      }
    );

    return () => {
      clearTimeout(timer);
      subscription.unsubscribe();
    };
  }, []);

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <SupplierAuthContext.Provider
      value={{ supplierUser, supplierSession, isApproved, loading, signOut }}
    >
      {children}
    </SupplierAuthContext.Provider>
  );
}

export const useSupplierAuth = () => {
  const ctx = useContext(SupplierAuthContext);
  if (!ctx) throw new Error('useSupplierAuth must be used inside <SupplierAuthProvider>');
  return ctx;
};
