import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, BarChart3, ArrowRight, Building2, Users } from 'lucide-react';

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: (i) => ({ opacity: 1, y: 0, transition: { delay: i * 0.15, duration: 0.5, ease: [0.22, 1, 0.36, 1] } }),
};

function RoleCard({ icon: Icon, title, subtitle, description, accentColor, accentBg, onClick, delay }) {
  return (
    <motion.div
      custom={delay}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover={{ y: -6, boxShadow: '0 20px 60px rgba(0,0,0,0.12)' }}
      onClick={onClick}
      style={{
        background: 'white',
        border: '1.5px solid #E5E7EB',
        borderRadius: 20,
        padding: '40px 36px',
        cursor: 'pointer',
        flex: 1,
        minWidth: 280,
        maxWidth: 380,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        transition: 'border-color 0.2s',
        boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = accentColor; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#E5E7EB'; }}
    >
      {/* Top accent bar */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: `linear-gradient(90deg, ${accentColor}, ${accentColor}88)`, borderRadius: '20px 20px 0 0' }} />

      {/* Icon */}
      <div style={{
        width: 80, height: 80, borderRadius: 24, background: accentBg,
        display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24,
      }}>
        <Icon size={38} color={accentColor} strokeWidth={1.6} />
      </div>

      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', color: accentColor, textTransform: 'uppercase', marginBottom: 8 }}>
        {subtitle}
      </div>
      <h2 style={{ fontSize: 26, fontWeight: 800, color: '#111827', marginBottom: 14 }}>{title}</h2>
      <p style={{ fontSize: 14, color: '#6B7280', lineHeight: 1.7, marginBottom: 32 }}>{description}</p>

      <button
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: accentColor, color: 'white',
          border: 'none', borderRadius: 10, padding: '12px 28px',
          fontSize: 14, fontWeight: 700, cursor: 'pointer',
          boxShadow: `0 4px 16px ${accentColor}40`,
          transition: 'opacity 0.15s',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.88'; }}
        onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
      >
        Continue <ArrowRight size={16} />
      </button>
    </motion.div>
  );
}

export default function RoleSelect() {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: '100vh', background: '#F9FAFB', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px 20px' }}>
      {/* Background decoration */}
      <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        <div style={{ position: 'absolute', top: -120, right: -120, width: 480, height: 480, background: 'radial-gradient(circle, rgba(37,99,235,0.07) 0%, transparent 70%)', borderRadius: '50%' }} />
        <div style={{ position: 'absolute', bottom: -120, left: -120, width: 480, height: 480, background: 'radial-gradient(circle, rgba(16,185,129,0.06) 0%, transparent 70%)', borderRadius: '50%' }} />
      </div>

      {/* Logo */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ textAlign: 'center', marginBottom: 56 }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 32 }}>
          <div className="animate-float" style={{ width: 52, height: 52, background: 'linear-gradient(135deg, #2563EB, #7C3AED)', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldCheck size={26} color="white" strokeWidth={2} />
          </div>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#111827' }}>SupplyShield AI</div>
            <div style={{ fontSize: 11, color: '#6B7280', fontWeight: 500, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Enterprise Platform</div>
          </div>
        </div>

        <h1 style={{ fontSize: 36, fontWeight: 800, color: '#111827', marginBottom: 12 }}>
          Welcome. Who are you?
        </h1>
        <p style={{ fontSize: 16, color: '#6B7280', maxWidth: 420, margin: '0 auto' }}>
          Select your role to access the right workspace. Each portal is tailored to your responsibilities.
        </p>
      </motion.div>

      {/* Role Cards */}
      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 840, width: '100%' }}>
        <RoleCard
          icon={BarChart3}
          title="Manufacturer"
          subtitle="Operations Team"
          description="Access the full SupplyShield AI platform — risk monitoring, disruption intelligence, supplier oversight, AI orchestration, and executive analytics."
          accentColor="#2563EB"
          accentBg="#EFF6FF"
          delay={0}
          onClick={() => navigate('/login')}
        />
        <RoleCard
          icon={Building2}
          title="Supplier"
          subtitle="Partner Organization"
          description="Manage your company profile, update production capacity, track shipments, report incidents, and monitor your AI-generated performance scores."
          accentColor="#10B981"
          accentBg="#ECFDF5"
          delay={1}
          onClick={() => navigate('/supplier/login')}
        />
      </div>

      {/* Registration links below the cards */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        style={{ marginTop: 28, display: 'flex', gap: 40, flexWrap: 'wrap', justifyContent: 'center' }}
      >
        <div style={{ textAlign: 'center' }}>
          <span style={{ fontSize: 13, color: '#9CA3AF' }}>New manufacturer?{' '}</span>
          <button
            onClick={() => navigate('/signup')}
            style={{ fontSize: 13, color: '#2563EB', fontWeight: 700, background: 'none', border: 'none', cursor: 'pointer' }}
          >
            Register as Manufacturer
          </button>
        </div>
        <div style={{ textAlign: 'center' }}>
          <span style={{ fontSize: 13, color: '#9CA3AF' }}>Supplier? Registration is by{' '}</span>
          <span style={{ fontSize: 13, color: '#10B981', fontWeight: 700 }}>invitation only</span>
        </div>
      </motion.div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        style={{ marginTop: 48, fontSize: 13, color: '#9CA3AF', textAlign: 'center' }}
      >
        Secured by SupplyShield AI · Enterprise-grade encryption · SOC 2 Compliant
      </motion.p>
    </div>
  );
}
