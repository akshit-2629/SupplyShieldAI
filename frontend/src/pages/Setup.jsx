/**
 * Setup.jsx — Main page for the manufacturer onboarding wizard.
 *
 * Manages step navigation, loads existing progress on mount,
 * and renders the current step component inside a full-screen layout.
 */

import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useSetupStore } from '../store/setupStore';
import { getSetupStatus, getCompany, listFactories, listWarehouses, listProducts, listComponents } from '../services/manufacturerApi';

import WizardSidebar   from '../components/setup/WizardSidebar';
import Step1Company    from '../components/setup/Step1Company';
import Step2Factories  from '../components/setup/Step2Factories';
import Step3Warehouses from '../components/setup/Step3Warehouses';
import Step4Products   from '../components/setup/Step4Products';
import Step5Components from '../components/setup/Step5Components';
import Step6Review     from '../components/setup/Step6Review';
import Step7Finish     from '../components/setup/Step7Finish';

export default function Setup() {
  const { user } = useAuth();
  const {
    currentStep, setCurrentStep,
    setCompany, setFactories, setWarehouses, setProducts, setComponents,
  } = useSetupStore();

  const [status, setStatus]     = useState(null); // null = checking
  const [loading, setLoading]   = useState(true);

  // On mount: check setup status and pre-populate existing data
  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const s = await getSetupStatus();
        setStatus(s);
        if (s.complete) return; // will redirect

        // Resume: set current step from server
        if (s.current_step > 1) {
          setCurrentStep(s.current_step);
        }

        // Pre-populate store with existing data (resume support)
        const [company, factories, warehouses, products, components] = await Promise.allSettled([
          s.company_exists ? getCompany() : Promise.resolve(null),
          listFactories(),
          listWarehouses(),
          listProducts(),
          listComponents(),
        ]);

        if (company.status === 'fulfilled' && company.value)
          setCompany(company.value);
        if (factories.status  === 'fulfilled') setFactories(factories.value  || []);
        if (warehouses.status === 'fulfilled') setWarehouses(warehouses.value || []);
        if (products.status   === 'fulfilled') setProducts(products.value    || []);
        if (components.status === 'fulfilled') setComponents(components.value || []);
      } catch (_) {
        // Treat API failure as "not set up" — user can start from scratch
        setStatus({ complete: false, current_step: 1 });
      } finally {
        setLoading(false);
      }
    })();
  }, [user]);

  // ── Loading ──
  if (loading) {
    return (
      <div style={{
        minHeight: '100vh', background: '#F9FAFB',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 16,
      }}>
        <div style={{
          width: 56, height: 56,
          background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
          borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
          animation: 'float 2s ease-in-out infinite',
        }}>
          <ShieldCheck size={28} color="white" strokeWidth={2} />
        </div>
        <span style={{ fontSize: 14, color: '#6B7280', fontWeight: 500 }}>
          Loading your configuration…
        </span>
      </div>
    );
  }

  // ── Redirect if already complete ──
  if (status?.complete) {
    return <Navigate to="/dashboard" replace />;
  }

  // ── Navigation helpers ──
  const goNext = () =>
    setCurrentStep(Math.min(currentStep + 1, 7));

  const goBack = () =>
    setCurrentStep(Math.max(currentStep - 1, 1));

  const jumpTo = (step) =>
    setCurrentStep(step);

  // ── Render current step ──
  const stepProps = { onNext: goNext, onBack: goBack };

  const StepComponent = {
    1: <Step1Company    {...stepProps} />,
    2: <Step2Factories  {...stepProps} />,
    3: <Step3Warehouses {...stepProps} />,
    4: <Step4Products   {...stepProps} />,
    5: <Step5Components {...stepProps} />,
    6: <Step6Review     {...stepProps} onJumpTo={jumpTo} />,
    7: <Step7Finish     onBack={goBack} />,
  }[currentStep];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Sidebar + content split */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <WizardSidebar currentStep={currentStep} />

        {/* Scrollable content area */}
        <main style={{
          flex: 1,
          overflowY: 'auto',
          background: '#F8FAFF',
          padding: '48px 40px',
        }}>
          {StepComponent}
        </main>
      </div>
    </div>
  );
}
