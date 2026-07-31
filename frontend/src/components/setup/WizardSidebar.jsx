/**
 * WizardSidebar.jsx — Left panel for the setup wizard.
 * Shows step list, completion status, and a progress bar.
 * On mobile (<768px) collapses to a compact top strip.
 */

import { CheckCircle2, Circle, Loader } from 'lucide-react';

const STEPS = [
  { n: 1, label: 'Company Information', desc: 'Your organisation details' },
  { n: 2, label: 'Factories',           desc: 'Manufacturing locations' },
  { n: 3, label: 'Warehouses',          desc: 'Storage facilities' },
  { n: 4, label: 'Products',            desc: 'What you manufacture' },
  { n: 5, label: 'Components',          desc: 'Bill of materials' },
  { n: 6, label: 'Review',              desc: 'Confirm everything' },
  { n: 7, label: 'Activate',            desc: 'Launch AI monitoring' },
];

export default function WizardSidebar({ currentStep, completedUpTo }) {
  const pct = Math.round(((currentStep - 1) / (STEPS.length - 1)) * 100);

  return (
    <>
      {/* ── Desktop sidebar ── */}
      <aside style={{
        width: 260,
        minWidth: 260,
        background: '#0F172A',
        display: 'flex',
        flexDirection: 'column',
        padding: '40px 24px',
        position: 'relative',
        overflow: 'hidden',
      }} className="hidden md:flex">
        {/* Background glow */}
        <div style={{
          position: 'absolute', top: -80, left: -80, width: 300, height: 300,
          background: 'radial-gradient(circle, rgba(37,99,235,0.18) 0%, transparent 70%)',
          borderRadius: '50%', pointerEvents: 'none',
        }} />

        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 40 }}>
          <div style={{
            width: 36, height: 36,
            background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
            borderRadius: 10,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 800, color: 'white', letterSpacing: '-0.01em' }}>
              SupplyShield AI
            </div>
            <div style={{ fontSize: 10, color: '#64748B', fontWeight: 500 }}>Setup Wizard</div>
          </div>
        </div>

        {/* Steps */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 0 }}>
          {STEPS.map((step, i) => {
            const done    = step.n < currentStep;
            const active  = step.n === currentStep;
            const locked  = step.n > currentStep;

            return (
              <div key={step.n} style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                {/* Column: icon + connector line */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  {/* Step circle */}
                  <div style={{
                    width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: done ? '#2563EB' : active ? 'rgba(37,99,235,0.2)' : 'rgba(255,255,255,0.05)',
                    border: active ? '2px solid #2563EB' : done ? 'none' : '2px solid rgba(255,255,255,0.1)',
                    transition: 'all 0.3s ease',
                  }}>
                    {done
                      ? <CheckCircle2 size={14} color="white" />
                      : active
                        ? <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#2563EB' }} />
                        : <span style={{ fontSize: 11, fontWeight: 600, color: '#475569' }}>{step.n}</span>
                    }
                  </div>
                  {/* Connector line */}
                  {i < STEPS.length - 1 && (
                    <div style={{
                      width: 2, height: 36,
                      background: done ? '#2563EB' : 'rgba(255,255,255,0.07)',
                      margin: '4px 0',
                      transition: 'background 0.3s ease',
                    }} />
                  )}
                </div>

                {/* Label */}
                <div style={{ paddingTop: 4, paddingBottom: i < STEPS.length - 1 ? 0 : 0 }}>
                  <div style={{
                    fontSize: 13, fontWeight: active ? 700 : 500,
                    color: active ? 'white' : done ? '#94A3B8' : '#475569',
                    transition: 'color 0.2s',
                    lineHeight: 1.3,
                  }}>
                    {step.label}
                  </div>
                  {active && (
                    <div style={{ fontSize: 11, color: '#64748B', marginTop: 2 }}>
                      {step.desc}
                    </div>
                  )}
                  {/* Spacer matching connector height */}
                  <div style={{ height: i < STEPS.length - 1 ? 36 : 0 }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div style={{ marginTop: 32 }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            marginBottom: 8,
          }}>
            <span style={{ fontSize: 11, color: '#64748B', fontWeight: 500 }}>Progress</span>
            <span style={{ fontSize: 11, color: '#94A3B8', fontWeight: 600 }}>{pct}%</span>
          </div>
          <div style={{
            height: 4, borderRadius: 4,
            background: 'rgba(255,255,255,0.07)',
            overflow: 'hidden',
          }}>
            <div style={{
              height: '100%',
              width: `${pct}%`,
              background: 'linear-gradient(90deg, #2563EB, #7C3AED)',
              borderRadius: 4,
              transition: 'width 0.4s ease',
            }} />
          </div>
        </div>
      </aside>

      {/* ── Mobile top strip ── */}
      <div style={{
        background: '#0F172A',
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }} className="flex md:hidden">
        <div style={{
          fontSize: 13, fontWeight: 700, color: 'white', whiteSpace: 'nowrap',
        }}>
          Step {currentStep} / {STEPS.length}
        </div>
        <div style={{ flex: 1, height: 4, borderRadius: 4, background: 'rgba(255,255,255,0.1)' }}>
          <div style={{
            height: '100%', width: `${pct}%`,
            background: 'linear-gradient(90deg, #2563EB, #7C3AED)',
            borderRadius: 4, transition: 'width 0.4s ease',
          }} />
        </div>
        <div style={{ fontSize: 11, color: '#64748B', fontWeight: 600, whiteSpace: 'nowrap' }}>
          {STEPS[currentStep - 1]?.label}
        </div>
      </div>
    </>
  );
}
