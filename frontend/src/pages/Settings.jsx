import { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Shield, Bell, Key, Sliders, Save, Copy, Eye, EyeOff } from 'lucide-react';

const tabs = [
  { key: 'profile', label: 'Profile', icon: User },
  { key: 'security', label: 'Security', icon: Shield },
  { key: 'notifications', label: 'Notifications', icon: Bell },
  { key: 'apikeys', label: 'API Keys', icon: Key },
  { key: 'preferences', label: 'Preferences', icon: Sliders },
];

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile');
  const [showApiKey, setShowApiKey] = useState(false);
  const [saved, setSaved] = useState(false);

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 900 }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Settings</h1>
        <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Manage your account, security, and platform preferences</p>
      </motion.div>

      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
        {/* Sidebar tabs */}
        <motion.div initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} className="card" style={{ padding: 8, width: 200, flexShrink: 0 }}>
          {tabs.map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 8, padding: '9px 12px', borderRadius: 7, border: 'none', background: activeTab === tab.key ? '#EFF6FF' : 'transparent', color: activeTab === tab.key ? '#2563EB' : '#6B7280', fontSize: 13.5, fontWeight: activeTab === tab.key ? 600 : 400, cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s', marginBottom: 2 }}>
              <tab.icon size={15} />
              {tab.label}
            </button>
          ))}
        </motion.div>

        {/* Tab content */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card" style={{ flex: 1, padding: 24 }}>
          {activeTab === 'profile' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#111827', marginBottom: 4 }}>Profile Information</div>
              {/* Avatar */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'linear-gradient(135deg,#2563EB,#7C3AED)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: 22, fontWeight: 800, color: 'white' }}>AK</span>
                </div>
                <div>
                  <button style={{ background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 7, padding: '7px 14px', fontSize: 13, fontWeight: 500, cursor: 'pointer', marginBottom: 4 }}>Change Avatar</button>
                  <div style={{ fontSize: 11, color: '#9CA3AF' }}>JPG, PNG up to 2MB</div>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                {[
                  { label: 'Full Name', value: 'Akshit Kumar', type: 'text' },
                  { label: 'Job Title', value: 'Chief Risk Officer', type: 'text' },
                  { label: 'Email', value: 'akshit@supplyshield.ai', type: 'email' },
                  { label: 'Organization', value: 'SupplyShield Inc.', type: 'text' },
                ].map(f => (
                  <div key={f.label}>
                    <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>{f.label}</label>
                    <input defaultValue={f.value} type={f.type} style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '8px 12px', fontSize: 13, color: '#374151', outline: 'none', transition: 'border 0.15s' }}
                      onFocus={e => e.target.style.borderColor = '#2563EB'}
                      onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>Security Settings</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {['Current Password', 'New Password', 'Confirm New Password'].map(f => (
                  <div key={f}>
                    <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>{f}</label>
                    <input type="password" placeholder="••••••••" style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '8px 12px', fontSize: 13, outline: 'none' }}
                      onFocus={e => e.target.style.borderColor = '#2563EB'}
                      onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                    />
                  </div>
                ))}
                <div style={{ background: '#F9FAFB', border: '1px solid #F3F4F6', borderRadius: 8, padding: '12px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>Two-Factor Authentication</div>
                    <div style={{ fontSize: 12, color: '#9CA3AF' }}>Add extra layer of security to your account</div>
                  </div>
                  <div style={{ width: 44, height: 24, borderRadius: 12, background: '#2563EB', position: 'relative', cursor: 'pointer' }}>
                    <div style={{ width: 18, height: 18, borderRadius: '50%', background: 'white', position: 'absolute', top: 3, right: 3, boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>Notification Preferences</div>
              {[
                { label: 'Critical Risk Alerts', sub: 'Immediate notifications for critical disruptions', on: true },
                { label: 'Daily Risk Summary', sub: 'Morning digest of supply chain risk status', on: true },
                { label: 'Supplier Status Changes', sub: 'When supplier risk scores change significantly', on: true },
                { label: 'Report Generation', sub: 'When AI-generated reports are ready', on: false },
                { label: 'Inventory Warnings', sub: 'When inventory falls below threshold', on: true },
                { label: 'AI Agent Activity', sub: 'Status updates from AI orchestration workflows', on: false },
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < 5 ? '1px solid #F3F4F6' : 'none' }}>
                  <div>
                    <div style={{ fontSize: 13.5, fontWeight: 500, color: '#111827' }}>{item.label}</div>
                    <div style={{ fontSize: 12, color: '#9CA3AF' }}>{item.sub}</div>
                  </div>
                  <div style={{ width: 44, height: 24, borderRadius: 12, background: item.on ? '#2563EB' : '#E5E7EB', position: 'relative', cursor: 'pointer', transition: 'background 0.2s', flexShrink: 0 }}>
                    <div style={{ width: 18, height: 18, borderRadius: '50%', background: 'white', position: 'absolute', top: 3, left: item.on ? 23 : 3, transition: 'left 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'apikeys' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>API Keys</div>
              {[{ label: 'Platform API Key', key: 'ss_live_k9xm2p4r8n1q...', active: true }, { label: 'Webhook Secret', key: 'whsec_7t3bv9wx4kz...', active: true }].map((k, i) => (
                <div key={i} style={{ background: '#FAFAFA', border: '1px solid #F3F4F6', borderRadius: 8, padding: '14px 16px' }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#374151', marginBottom: 8 }}>{k.label}</div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <div style={{ flex: 1, background: 'white', border: '1px solid #E5E7EB', borderRadius: 7, padding: '7px 12px', fontSize: 13, fontFamily: 'monospace', color: '#374151', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {showApiKey ? k.key + 'a7k3m9x2' : k.key}
                    </div>
                    <button onClick={() => setShowApiKey(!showApiKey)} style={{ background: '#F3F4F6', border: '1px solid #E5E7EB', borderRadius: 7, padding: '7px 10px', cursor: 'pointer' }}>
                      {showApiKey ? <EyeOff size={14} color="#6B7280" /> : <Eye size={14} color="#6B7280" />}
                    </button>
                    <button style={{ background: '#F3F4F6', border: '1px solid #E5E7EB', borderRadius: 7, padding: '7px 10px', cursor: 'pointer' }}>
                      <Copy size={14} color="#6B7280" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'preferences' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}>Platform Preferences</div>
              {[
                { label: 'Default Dashboard', options: ['Executive View', 'Risk View', 'Operational View'] },
                { label: 'Currency', options: ['USD ($)', 'EUR (€)', 'GBP (£)'] },
                { label: 'Risk Threshold', options: ['Conservative (60)', 'Standard (70)', 'Aggressive (80)'] },
                { label: 'Date Format', options: ['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'] },
              ].map(f => (
                <div key={f.label}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>{f.label}</label>
                  <select style={{ width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '8px 12px', fontSize: 13, color: '#374151', background: 'white', outline: 'none', appearance: 'none', cursor: 'pointer' }}>
                    {f.options.map(o => <option key={o}>{o}</option>)}
                  </select>
                </div>
              ))}
            </div>
          )}

          {/* Save button */}
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid #F3F4F6' }}>
            <button onClick={handleSave} style={{ display: 'flex', alignItems: 'center', gap: 6, background: saved ? '#059669' : '#111827', color: 'white', border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 13, fontWeight: 600, cursor: 'pointer', transition: 'background 0.2s' }}>
              <Save size={14} /> {saved ? 'Saved!' : 'Save Changes'}
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
