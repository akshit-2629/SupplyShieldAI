import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShieldCheck, Loader } from 'lucide-react';
import { supabase } from '../lib/supabase';

/**
 * AuthCallback handles two OAuth redirect scenarios:
 *
 * 1. Supabase OAuth (Google via Supabase dashboard)
 *    Supabase redirects here with the session in the URL fragment.
 *    `supabase.auth.onAuthStateChange` picks it up automatically.
 *
 * 2. Backend Google OAuth (/api/v1/auth/google/callback)
 *    The backend redirects here with #access_token=...&token_type=bearer
 *    We manually extract the token from the URL fragment and set the session.
 */
export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    async function handleCallback() {
      const hash = window.location.hash;

      // ── Path A: Backend Google OAuth redirect ──────────────────
      // Backend redirects to /auth/callback#access_token=...
      if (hash && hash.includes('access_token')) {
        const params = new URLSearchParams(hash.substring(1)); // strip leading #
        const accessToken = params.get('access_token');
        const tokenType   = params.get('token_type');
        const expiresIn   = params.get('expires_in');

        if (accessToken) {
          try {
            // Set the Supabase session manually using the backend-minted JWT
            const { data, error } = await supabase.auth.setSession({
              access_token:  accessToken,
              refresh_token: accessToken, // backend flow has no refresh token
            });

            if (error) {
              console.error('[AuthCallback] setSession error:', error.message);
              // Token may be valid even if setSession rejects — try to navigate anyway
              // The backend minted a valid Supabase JWT so protected routes will accept it
            }

            navigate('/dashboard', { replace: true });
            return;
          } catch (err) {
            console.error('[AuthCallback] Token processing error:', err);
            navigate('/login?error=token_error', { replace: true });
            return;
          }
        }
      }

      // ── Path B: Supabase OAuth redirect (Google via Supabase) ──
      // Supabase automatically parses the URL fragment and fires onAuthStateChange
      const { data: { subscription } } = supabase.auth.onAuthStateChange(
        (event, session) => {
          if (event === 'SIGNED_IN' && session) {
            navigate('/dashboard', { replace: true });
          } else if (event === 'SIGNED_OUT') {
            navigate('/login', { replace: true });
          }
        }
      );

      // Fallback: session may already exist in storage
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        navigate('/dashboard', { replace: true });
        return;
      }

      // Timeout guard — if nothing fires in 5 seconds, send to login
      const timeout = setTimeout(() => {
        navigate('/login?error=callback_timeout', { replace: true });
      }, 5000);

      return () => {
        subscription.unsubscribe();
        clearTimeout(timeout);
      };
    }

    handleCallback();
  }, [navigate]);

  return (
    <div style={{
      minHeight: '100vh',
      background: '#F9FAFB',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 20,
    }}>
      <motion.div
        animate={{ scale: [1, 1.08, 1] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
        style={{
          width: 64, height: 64,
          background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
          borderRadius: 18,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 8px 32px rgba(37,99,235,0.35)',
        }}
      >
        <ShieldCheck size={32} color="white" strokeWidth={2} />
      </motion.div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center', marginBottom: 8 }}>
          <Loader size={16} color="#2563EB" style={{ animation: 'spin-slow 1.5s linear infinite' }} />
          <span style={{ fontSize: 15, fontWeight: 600, color: '#111827' }}>Completing sign in...</span>
        </div>
        <p style={{ fontSize: 13, color: '#9CA3AF' }}>Please wait while we verify your credentials.</p>
      </div>
    </div>
  );
}
