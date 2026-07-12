import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck, Globe, Network, Cpu, BarChart3, Bell,
  Package, ArrowRight, CheckCircle, Zap, ChevronRight,
  Building2, TrendingDown, AlertTriangle
} from 'lucide-react';

const features = [
  {
    icon: Globe,
    color: '#2563EB',
    bg: '#EFF6FF',
    title: 'Global Risk Map',
    desc: 'Monitor disruptions worldwide in real-time across 150+ countries with geospatial intelligence.',
  },
  {
    icon: Network,
    color: '#7C3AED',
    bg: '#EDE9FE',
    title: 'Knowledge Graph',
    desc: 'Visualize supplier-component-product dependencies and instantly trace disruption blast radius.',
  },
  {
    icon: Cpu,
    color: '#0891B2',
    bg: '#ECFEFF',
    title: 'AI Agent Orchestration',
    desc: 'Seven specialized AI agents work in parallel to detect, assess, and respond to supply chain risks.',
  },
  {
    icon: BarChart3,
    color: '#059669',
    bg: '#D1FAE5',
    title: 'Inventory Intelligence',
    desc: 'Predict stockout timelines with Monte Carlo simulations and get pre-emptive reorder alerts.',
  },
  {
    icon: Building2,
    color: '#D97706',
    bg: '#FEF3C7',
    title: 'Supplier Discovery',
    desc: 'AI-ranked alternative supplier recommendations with quality, cost, and risk scoring.',
  },
  {
    icon: AlertTriangle,
    color: '#DC2626',
    bg: '#FEE2E2',
    title: 'Disruption Monitor',
    desc: 'Continuous scanning of news, geopolitical signals, and port data for early warnings.',
  },
];

const stats = [
  { value: '150+', label: 'Countries Monitored' },
  { value: '10K+', label: 'Suppliers Tracked' },
  { value: '7', label: 'Specialized AI Agents' },
  { value: '<2min', label: 'Alert Response Time' },
];

const trustedBy = ['Accenture', 'Deloitte', 'McKinsey', 'Siemens', 'Bosch', 'BASF'];

export default function Landing() {
  const navigate = useNavigate();
  const { user, loading } = useAuth();

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (!loading && user) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, loading, navigate]);

  return (
    <div style={{ minHeight: '100vh', background: '#FFFFFF', fontFamily: 'Inter, sans-serif' }}>

      {/* ── Nav ── */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(12px)',
        borderBottom: '1px solid #F3F4F6',
        padding: '0 5%', height: 64,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34,
            background: 'linear-gradient(135deg, #2563EB, #7C3AED)',
            borderRadius: 9, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <ShieldCheck size={18} color="white" strokeWidth={2} />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 800, color: '#111827', letterSpacing: '-0.01em' }}>SupplyShield AI</div>
            <div style={{ fontSize: 9, fontWeight: 600, color: '#9CA3AF', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Intelligence Platform</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={() => navigate('/login')}
            style={{ background: 'none', border: 'none', fontSize: 14, fontWeight: 500, color: '#6B7280', cursor: 'pointer', padding: '8px 14px', borderRadius: 8, transition: 'all 0.15s' }}
            onMouseEnter={e => { e.currentTarget.style.background = '#F5F5F5'; e.currentTarget.style.color = '#111827'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = '#6B7280'; }}
          >
            Sign in
          </button>
          <button
            onClick={() => navigate('/signup')}
            style={{ background: 'linear-gradient(135deg, #2563EB, #7C3AED)', color: 'white', border: 'none', borderRadius: 9, padding: '9px 18px', fontSize: 14, fontWeight: 600, cursor: 'pointer', boxShadow: '0 4px 14px rgba(37,99,235,0.3)', transition: 'all 0.2s' }}
            onMouseEnter={e => e.currentTarget.style.opacity = '0.9'}
            onMouseLeave={e => e.currentTarget.style.opacity = '1'}
          >
            Get Started Free
          </button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section style={{ padding: '96px 5% 80px', maxWidth: 1200, margin: '0 auto', textAlign: 'center' }}>
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 20, padding: '5px 14px', marginBottom: 32 }}
        >
          <Zap size={12} color="#2563EB" />
          <span style={{ fontSize: 12, fontWeight: 600, color: '#2563EB' }}>Powered by 7 Autonomous AI Agents</span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.05 }}
          style={{ fontSize: 'clamp(36px, 6vw, 68px)', fontWeight: 900, color: '#111827', letterSpacing: '-0.03em', lineHeight: 1.1, marginBottom: 24 }}
        >
          Know Every Risk.{' '}
          <span style={{ background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 60%, #DB2777 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
            Before It Strikes.
          </span>
        </motion.h1>

        {/* Sub */}
        <motion.p
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
          style={{ fontSize: 'clamp(16px, 2vw, 20px)', color: '#6B7280', maxWidth: 640, margin: '0 auto 44px', lineHeight: 1.7 }}
        >
          SupplyShield AI autonomously monitors global supply chains, detects disruptions in real-time,
          and delivers executive-ready intelligence so you can act before competitors even know there's a problem.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 }}
          style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}
        >
          <button
            onClick={() => navigate('/signup')}
            style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', color: 'white', border: 'none', borderRadius: 12, padding: '14px 28px', fontSize: 15, fontWeight: 700, cursor: 'pointer', boxShadow: '0 6px 24px rgba(37,99,235,0.35)', transition: 'all 0.2s' }}
            onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
            onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
          >
            Start Free Trial <ArrowRight size={16} />
          </button>
          <button
            onClick={() => navigate('/login')}
            style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'white', color: '#374151', border: '1.5px solid #E5E7EB', borderRadius: 12, padding: '14px 28px', fontSize: 15, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s' }}
            onMouseEnter={e => { e.currentTarget.style.background = '#F9FAFB'; e.currentTarget.style.borderColor = '#D1D5DB'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'white'; e.currentTarget.style.borderColor = '#E5E7EB'; }}
          >
            Sign In <ChevronRight size={16} />
          </button>
        </motion.div>
      </section>

      {/* ── Dashboard Preview ── */}
      <motion.section
        initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.25 }}
        style={{ padding: '0 5% 80px', maxWidth: 1200, margin: '0 auto' }}
      >
        <div style={{
          background: 'linear-gradient(135deg, #F0F4FF 0%, #FAF0FE 100%)',
          border: '1px solid #E5E7EB',
          borderRadius: 20,
          padding: 24,
          boxShadow: '0 24px 80px rgba(37,99,235,0.1)',
        }}>
          {/* Fake browser chrome */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 16, alignItems: 'center' }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#FCA5A5' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#FCD34D' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#6EE7B7' }} />
            <div style={{ flex: 1, height: 26, background: 'white', borderRadius: 6, marginLeft: 8, display: 'flex', alignItems: 'center', paddingLeft: 10, fontSize: 11, color: '#9CA3AF', border: '1px solid #F3F4F6' }}>
              app.supplyshield.ai/dashboard
            </div>
          </div>
          {/* Mini dashboard mockup */}
          <div style={{ background: '#F9FAFB', borderRadius: 12, padding: 16, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
            {[
              { label: 'Active Disruptions', value: '8', color: '#DC2626', bg: '#FEE2E2', icon: AlertTriangle },
              { label: 'Critical Risks', value: '2', color: '#9A3412', bg: '#FEF3C7', icon: TrendingDown },
              { label: 'Affected Suppliers', value: '47', color: '#D97706', bg: '#FEF9C3', icon: Building2 },
              { label: 'AI Alerts Today', value: '14', color: '#2563EB', bg: '#EFF6FF', icon: Bell },
            ].map(kpi => {
              const Icon = kpi.icon;
              return (
                <div key={kpi.label} style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 10, padding: '14px 16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: 10, color: '#9CA3AF', fontWeight: 500 }}>{kpi.label}</span>
                    <div style={{ width: 28, height: 28, background: kpi.bg, borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Icon size={13} color={kpi.color} />
                    </div>
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: '#111827' }}>{kpi.value}</div>
                </div>
              );
            })}
          </div>
          <div style={{ marginTop: 10, background: 'white', border: '1px solid #E5E7EB', borderRadius: 10, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#DC2626', animation: 'pulse-ring 1.5s ease-out infinite' }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: '#991B1B' }}>CRITICAL:</span>
            <span style={{ fontSize: 12, color: '#B91C1C' }}>TSMC Fab 18 fire affecting 63 suppliers — AI agents actively assessing impact</span>
          </div>
        </div>
      </motion.section>

      {/* ── Stats ── */}
      <section style={{ background: 'linear-gradient(135deg, #2563EB, #7C3AED)', padding: '56px 5%' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 40, textAlign: 'center' }}>
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }} viewport={{ once: true }}
            >
              <div style={{ fontSize: 'clamp(32px, 5vw, 48px)', fontWeight: 900, color: 'white', letterSpacing: '-0.02em' }}>{s.value}</div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.75)', marginTop: 4, fontWeight: 500 }}>{s.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section style={{ padding: '80px 5%', maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 56 }}>
          <motion.div
            initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#F3F4F6', borderRadius: 20, padding: '5px 14px', marginBottom: 16 }}
          >
            <span style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>Platform Capabilities</span>
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 800, color: '#111827', letterSpacing: '-0.02em', marginBottom: 16 }}
          >
            Everything you need to manage<br />supply chain risk at scale
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
            style={{ fontSize: 16, color: '#6B7280', maxWidth: 560, margin: '0 auto' }}
          >
            From real-time disruption detection to executive report generation — SupplyShield handles the entire intelligence lifecycle.
          </motion.p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }} viewport={{ once: true }}
                style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 14, padding: 24, transition: 'all 0.2s' }}
                onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 8px 32px rgba(0,0,0,0.08)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translateY(0)'; }}
              >
                <div style={{ width: 44, height: 44, background: f.bg, borderRadius: 11, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                  <Icon size={20} color={f.color} />
                </div>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#111827', marginBottom: 8 }}>{f.title}</div>
                <div style={{ fontSize: 14, color: '#6B7280', lineHeight: 1.6 }}>{f.desc}</div>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* ── Trusted by ── */}
      <section style={{ padding: '40px 5% 60px', borderTop: '1px solid #F3F4F6', borderBottom: '1px solid #F3F4F6', background: '#FAFAFA' }}>
        <p style={{ textAlign: 'center', fontSize: 12, fontWeight: 600, color: '#9CA3AF', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 28 }}>
          Trusted by enterprise supply chain teams at
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '16px 40px' }}>
          {trustedBy.map(company => (
            <div key={company} style={{ fontSize: 16, fontWeight: 700, color: '#9CA3AF', letterSpacing: '-0.01em' }}>{company}</div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{ padding: '80px 5%', textAlign: 'center' }}>
        <motion.div
          initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          style={{ maxWidth: 600, margin: '0 auto' }}
        >
          <h2 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 800, color: '#111827', letterSpacing: '-0.02em', marginBottom: 16 }}>
            Start protecting your supply chain today
          </h2>
          <p style={{ fontSize: 16, color: '#6B7280', marginBottom: 36, lineHeight: 1.6 }}>
            Join supply chain teams that use SupplyShield AI to turn uncertainty into competitive advantage.
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap', marginBottom: 24 }}>
            <button
              onClick={() => navigate('/signup')}
              style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', color: 'white', border: 'none', borderRadius: 12, padding: '14px 28px', fontSize: 15, fontWeight: 700, cursor: 'pointer', boxShadow: '0 6px 24px rgba(37,99,235,0.35)', transition: 'all 0.2s' }}
              onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
            >
              Create Free Account <ArrowRight size={16} />
            </button>
            <button
              onClick={() => navigate('/login')}
              style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'white', color: '#374151', border: '1.5px solid #E5E7EB', borderRadius: 12, padding: '14px 28px', fontSize: 15, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s' }}
              onMouseEnter={e => e.currentTarget.style.background = '#F9FAFB'}
              onMouseLeave={e => e.currentTarget.style.background = 'white'}
            >
              Sign In
            </button>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 24, flexWrap: 'wrap' }}>
            {['No credit card required', 'Free 14-day trial', 'Cancel anytime'].map(item => (
              <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#6B7280' }}>
                <CheckCircle size={14} color="#059669" />
                {item}
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ borderTop: '1px solid #F3F4F6', padding: '24px 5%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 24, height: 24, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldCheck size={12} color="white" strokeWidth={2} />
          </div>
          <span style={{ fontSize: 13, fontWeight: 700, color: '#374151' }}>SupplyShield AI</span>
        </div>
        <span style={{ fontSize: 12, color: '#9CA3AF' }}>© 2026 SupplyShield AI. All rights reserved.</span>
      </footer>
    </div>
  );
}
