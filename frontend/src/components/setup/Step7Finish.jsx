/**
 * Step7Finish.jsx — Final step: calls complete-setup API then redirects to /dashboard.
 * Shows an animated activation sequence.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, CheckCircle2, Loader, AlertCircle, Cpu, Network, BrainCircuit } from 'lucide-react';
import { useSetupStore } from '../../store/setupStore';
import { completeSetup } from '../../services/manufacturerApi';

const ACTIVATION_STEPS = [
  { icon: <CheckCircle2 size={16} />, label: 'Saving company configuration…'   },
  { icon: <Network     size={16} />, label: 'Generating supply chain graph…'   },
  { icon: <Cpu         size={16} />, label: 'Initialising Knowledge Graph…'    },
  { icon: <BrainCircuit size={16} />,label: 'Activating Master Orchestrator…'  },
  { icon: <ShieldCheck  size={16} />,label: 'Enabling AI disruption monitoring…'},
];

export default function Step7Finish({ onBack }) {
  const navigate   = useNavigate();
  const { reset }  = useSetupStore();
  const [phase, setPhase]   = useState('confirm'); // confirm | activating | done | error
  const [activStep, setActivStep] = useState(0);
  const [error, setError]   = useState('');

  async function activate() {
    setPhase('activating');
    setActivStep(0);

    // Animate through activation steps
    for (let i = 0; i < ACTIVATION_STEPS.length; i++) {
      setActivStep(i);
      await delay(700 + Math.random() * 400);
    }

    // Call the real API
    try {
      await completeSetup();
      setPhase('done');
      reset();
      // Redirect after 2 seconds so user sees success screen
      setTimeout(() => navigate('/dashboard', { replace: true }), 2000);
    } catch (e) {
      setError(e.message);
      setPhase('error');
    }
  }

  return (
    <div style={{
      maxWidth: 600, margin: '0 auto', textAlign: 'center',
      animation: 'slideUp 0.3s ease both',
    }}>
      {/* ── Confirm ── */}
      {phase === 'confirm' && (
        <>
          <div style={{ marginBottom: 32 }}>
            <div style={{
              width: 80, height: 80, borderRadius: '50%',
              background: 'linear-gradient(135deg, #EFF6FF, #DBEAFE)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 24px',
              border: '3px solid #DBEAFE',
            }}>
              <ShieldCheck size={36} color="#2563EB" />
            </div>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: '#EFF6FF', border: '1px solid #DBEAFE',
              borderRadius: 20, padding: '4px 12px', marginBottom: 16,
            }}>
              <ShieldCheck size={13} color="#2563EB" />
              <span style={{ fontSize: 12, fontWeight: 600, color: '#2563EB' }}>Step 7 of 7 — Activate</span>
            </div>
            <h1 style={{ fontSize: 28, fontWeight: 800, color: '#111827', marginBottom: 12 }}>
              Ready to Activate SupplyShield AI
            </h1>
            <p style={{ fontSize: 14, color: '#6B7280', lineHeight: 1.7, maxWidth: 480, margin: '0 auto' }}>
              Your supply chain is fully configured. Clicking <strong>Activate</strong> will save
              everything, generate your Knowledge Graph, and start real-time AI disruption monitoring.
            </p>
          </div>

          {/* What happens next */}
          <div style={{
            background: 'white', border: '1px solid #E5E7EB', borderRadius: 12,
            padding: '24px', marginBottom: 32, textAlign: 'left',
          }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 16 }}>
              What happens when you activate
            </div>
            {ACTIVATION_STEPS.map((s, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 0',
                borderBottom: i < ACTIVATION_STEPS.length - 1 ? '1px solid #F3F4F6' : 'none',
              }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8, background: '#EFF6FF',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#2563EB', flexShrink: 0,
                }}>{s.icon}</div>
                <span style={{ fontSize: 13, color: '#374151', fontWeight: 500 }}>
                  {s.label.replace('…', '')}
                </span>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button onClick={onBack} style={{
              padding: '10px 20px', borderRadius: 8, border: '1.5px solid #E5E7EB',
              background: 'white', color: '#374151', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            }}>← Review</button>
            <button onClick={activate} style={{
              padding: '13px 32px', borderRadius: 10, border: 'none',
              background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
              color: 'white', fontSize: 15, fontWeight: 800, cursor: 'pointer',
              boxShadow: '0 4px 20px rgba(37,99,235,0.4)',
              letterSpacing: '-0.01em',
            }}>
              ⚡ Activate SupplyShield AI
            </button>
          </div>
        </>
      )}

      {/* ── Activating ── */}
      {phase === 'activating' && (
        <div style={{ padding: '40px 0' }}>
          <div style={{
            width: 80, height: 80, borderRadius: '50%',
            background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 28px',
            boxShadow: '0 0 40px rgba(37,99,235,0.35)',
            animation: 'float 2s ease-in-out infinite',
          }}>
            <ShieldCheck size={36} color="white" />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 8 }}>
            Activating SupplyShield AI
          </h2>
          <p style={{ fontSize: 13, color: '#9CA3AF', marginBottom: 36 }}>
            This takes just a moment…
          </p>

          <div style={{
            background: 'white', border: '1px solid #E5E7EB', borderRadius: 12, padding: '20px 24px',
          }}>
            {ACTIVATION_STEPS.map((s, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 0',
                borderBottom: i < ACTIVATION_STEPS.length - 1 ? '1px solid #F3F4F6' : 'none',
                opacity: i <= activStep ? 1 : 0.3,
                transition: 'opacity 0.4s ease',
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: i < activStep ? '#D1FAE5' : i === activStep ? '#EFF6FF' : '#F3F4F6',
                  color: i < activStep ? '#10B981' : i === activStep ? '#2563EB' : '#D1D5DB',
                }}>
                  {i < activStep ? <CheckCircle2 size={14} /> : i === activStep ? <Loader size={14} style={{ animation: 'spin 1s linear infinite' }} /> : s.icon}
                </div>
                <span style={{
                  fontSize: 13, fontWeight: i === activStep ? 700 : 500,
                  color: i < activStep ? '#10B981' : i === activStep ? '#111827' : '#9CA3AF',
                }}>{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Done ── */}
      {phase === 'done' && (
        <div style={{ padding: '40px 0' }}>
          <div style={{
            width: 80, height: 80, borderRadius: '50%',
            background: 'linear-gradient(135deg, #D1FAE5, #A7F3D0)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 24px',
            border: '3px solid #6EE7B7',
          }}>
            <CheckCircle2 size={38} color="#10B981" />
          </div>
          <h2 style={{ fontSize: 26, fontWeight: 800, color: '#111827', marginBottom: 10 }}>
            SupplyShield AI is Active 🎉
          </h2>
          <p style={{ fontSize: 14, color: '#6B7280', lineHeight: 1.7 }}>
            Your supply chain is now being monitored. Redirecting to the Executive Dashboard…
          </p>
          <div style={{ marginTop: 24 }}>
            <Loader size={18} color="#9CA3AF" style={{ animation: 'spin 1s linear infinite', display: 'inline' }} />
          </div>
        </div>
      )}

      {/* ── Error ── */}
      {phase === 'error' && (
        <div style={{ padding: '40px 0' }}>
          <div style={{
            width: 72, height: 72, borderRadius: '50%', background: '#FEF2F2',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 24px', border: '3px solid #FECACA',
          }}>
            <AlertCircle size={34} color="#EF4444" />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 8 }}>
            Activation failed
          </h2>
          <p style={{ fontSize: 13, color: '#6B7280', marginBottom: 20 }}>{error}</p>
          <button onClick={activate} style={{
            padding: '10px 24px', borderRadius: 8, border: 'none',
            background: '#2563EB', color: 'white', fontSize: 13, fontWeight: 700, cursor: 'pointer',
          }}>Retry</button>
        </div>
      )}
    </div>
  );
}

function delay(ms) { return new Promise((r) => setTimeout(r, ms)); }
