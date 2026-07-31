import { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Lock, Bell, Globe, Monitor, Shield, Smartphone, Save, Eye, EyeOff, CheckCircle2, LogOut, X } from 'lucide-react';
import PageHeader from '../../components/supplier/shared/PageHeader';
import { useSupplierAuth } from '../../context/SupplierAuthContext';
import { updateSupplierSettings } from '../../services/supplierApi';
import { supabase } from '../../lib/supabase';

const TABS = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'security', label: 'Security', icon: Lock },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'preferences', label: 'Preferences', icon: Globe },
  { id: 'sessions', label: 'Sessions', icon: Monitor },
];

const TIMEZONES = ['UTC', 'America/New_York', 'America/Chicago', 'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Asia/Singapore', 'Asia/Kolkata', 'Australia/Sydney'];
const LANGUAGES = ['English', 'Spanish', 'French', 'German', 'Japanese', 'Chinese (Simplified)', 'Portuguese', 'Arabic'];

function TabSection({ title, description, children }) {
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ padding: '16px 22px', borderBottom: '1px solid #F3F4F6' }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>{title}</h3>
        {description && <p style={{ fontSize: 12, color: '#9CA3AF', marginTop: 2 }}>{description}</p>}
      </div>
      <div style={{ padding: '20px 22px' }}>{children}</div>
    </div>
  );
}

function Toggle({ label, description, checked, onChange }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20, padding: '10px 0', borderBottom: '1px solid #F9FAFB' }}>
      <div>
        <div style={{ fontSize: 13.5, fontWeight: 500, color: '#111827' }}>{label}</div>
        {description && <div style={{ fontSize: 12, color: '#9CA3AF', marginTop: 2 }}>{description}</div>}
      </div>
      <button onClick={() => onChange(!checked)}
        style={{ width: 42, height: 24, borderRadius: 12, border: 'none', background: checked ? '#10B981' : '#E5E7EB', cursor: 'pointer', position: 'relative', transition: 'background 0.2s', flexShrink: 0 }}>
        <div style={{ width: 18, height: 18, borderRadius: '50%', background: 'white', position: 'absolute', top: 3, left: checked ? 21 : 3, transition: 'left 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }} />
      </button>
    </div>
  );
}

export default function SupplierSettings() {
  const { supplierUser } = useSupplierAuth();
  const meta = supplierUser?.user_metadata || {};
  const [activeTab, setActiveTab] = useState('profile');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Profile form
  const [profile, setProfile] = useState({ contactName: meta.contactName || '', email: supplierUser?.email || '', phone: meta.phone || '' });

  // Password form
  const [passwords, setPasswords] = useState({ current: '', newPass: '', confirm: '' });
  const [showPass, setShowPass] = useState({ current: false, new: false, confirm: false });
  const [pwError, setPwError] = useState('');

  // Notification prefs
  const [notifs, setNotifs] = useState({ emailAlerts: true, emailShipments: true, emailInventory: true, emailRecommendations: false, smsAlerts: false, smsShipments: false });

  // Preferences
  const [prefs, setPrefs] = useState({ timezone: 'UTC', language: 'English', dateFormat: 'MM/DD/YYYY' });

  async function save(data) {
    setSaving(true);
    try {
      const payload = {
        contact_name: data.contactName || data.contact_name,
        phone: data.phone,
      };
      await updateSupplierSettings(payload);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      console.error('Save settings error:', err);
      alert(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  }

  async function handlePasswordChange(e) {
    e.preventDefault();
    setPwError('');
    if (passwords.newPass !== passwords.confirm) { setPwError('New passwords do not match.'); return; }
    if (passwords.newPass.length < 8) { setPwError('Password must be at least 8 characters.'); return; }
    setSaving(true);
    const { error } = await supabase.auth.updateUser({ password: passwords.newPass });
    setSaving(false);
    if (error) { setPwError(error.message); return; }
    setPasswords({ current: '', newPass: '', confirm: '' });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  const inputSt = { width: '100%', border: '1px solid #E5E7EB', borderRadius: 7, padding: '9px 12px', fontSize: 13.5, outline: 'none', boxSizing: 'border-box' };
  const labelSt = { fontSize: 11, fontWeight: 700, color: '#6B7280', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' };

  const SaveBtn = ({ onClick }) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 6 }}>
      {saved && <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 13, color: '#10B981', fontWeight: 600 }}><CheckCircle2 size={14} /> Saved</div>}
      <button onClick={onClick} disabled={saving}
        style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '9px 20px', border: 'none', borderRadius: 8, fontSize: 13.5, fontWeight: 700, background: saving ? '#9CA3AF' : 'linear-gradient(135deg, #10B981, #059669)', color: 'white', cursor: saving ? 'not-allowed' : 'pointer' }}>
        <Save size={14} />{saving ? 'Saving…' : 'Save Changes'}
      </button>
    </div>
  );

  return (
    <div>
      <PageHeader title="Settings" description="Manage your account, security, notifications, and preferences" />

      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 20 }}>
        {/* Sidebar tabs */}
        <div className="card" style={{ padding: '10px', height: 'fit-content' }}>
          {TABS.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => setActiveTab(id)}
              style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 9, padding: '9px 12px', border: 'none', borderRadius: 7, background: activeTab === id ? '#ECFDF5' : 'transparent', color: activeTab === id ? '#059669' : '#6B7280', fontSize: 13.5, fontWeight: activeTab === id ? 700 : 400, cursor: 'pointer', textAlign: 'left', marginBottom: 2, transition: 'all 0.15s' }}>
              <Icon size={15} />
              {label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div>
          {activeTab === 'profile' && (
            <TabSection title="Profile Information" description="Update your personal and contact details">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                <div>
                  <label style={labelSt}>Full Name</label>
                  <input style={inputSt} value={profile.contactName} onChange={(e) => setProfile((p) => ({ ...p, contactName: e.target.value }))} onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} />
                </div>
                <div>
                  <label style={labelSt}>Email Address</label>
                  <input type="email" style={{ ...inputSt, background: '#F9FAFB', color: '#6B7280' }} value={profile.email} readOnly title="Email cannot be changed here" />
                </div>
                <div>
                  <label style={labelSt}>Phone Number</label>
                  <input style={inputSt} value={profile.phone} onChange={(e) => setProfile((p) => ({ ...p, phone: e.target.value }))} onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} />
                </div>
              </div>
              <SaveBtn onClick={() => save({ profile })} />
            </TabSection>
          )}

          {activeTab === 'security' && (
            <TabSection title="Change Password" description="Use a strong password you don't use elsewhere">
              <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 440 }}>
                {pwError && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#DC2626' }}>
                    <X size={14} /> {pwError}
                  </div>
                )}
                {[
                  { key: 'current', label: 'Current Password', type: 'current' },
                  { key: 'newPass', label: 'New Password', type: 'new' },
                  { key: 'confirm', label: 'Confirm New Password', type: 'confirm' },
                ].map(({ key, label, type }) => (
                  <div key={key}>
                    <label style={labelSt}>{label}</label>
                    <div style={{ position: 'relative' }}>
                      <input type={showPass[type] ? 'text' : 'password'} style={{ ...inputSt, paddingRight: 40 }}
                        value={passwords[key]} onChange={(e) => setPasswords((p) => ({ ...p, [key]: e.target.value }))}
                        placeholder="••••••••"
                        onFocus={(e) => e.target.style.borderColor='#10B981'} onBlur={(e) => e.target.style.borderColor='#E5E7EB'} />
                      <button type="button" onClick={() => setShowPass((p) => ({ ...p, [type]: !p[type] }))}
                        style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}>
                        {showPass[type] ? <EyeOff size={15} /> : <Eye size={15} />}
                      </button>
                    </div>
                  </div>
                ))}
                <SaveBtn onClick={handlePasswordChange} />
              </form>
            </TabSection>
          )}

          {activeTab === 'notifications' && (
            <>
              <TabSection title="Email Notifications" description="Choose which events send you an email">
                <Toggle label="Risk Alerts" description="High-priority risk alerts affecting your account" checked={notifs.emailAlerts} onChange={(v) => setNotifs((p) => ({ ...p, emailAlerts: v }))} />
                <Toggle label="Shipment Updates" description="Delivery confirmations and status changes" checked={notifs.emailShipments} onChange={(v) => setNotifs((p) => ({ ...p, emailShipments: v }))} />
                <Toggle label="Inventory Alerts" description="Low stock and safety stock warnings" checked={notifs.emailInventory} onChange={(v) => setNotifs((p) => ({ ...p, emailInventory: v }))} />
                <Toggle label="AI Recommendations" description="Weekly AI-generated improvement suggestions" checked={notifs.emailRecommendations} onChange={(v) => setNotifs((p) => ({ ...p, emailRecommendations: v }))} />
              </TabSection>
              <TabSection title="SMS Notifications" description="Text message alerts for critical events">
                <Toggle label="Critical Risk Alerts (SMS)" checked={notifs.smsAlerts} onChange={(v) => setNotifs((p) => ({ ...p, smsAlerts: v }))} />
                <Toggle label="Shipment Delivery (SMS)" checked={notifs.smsShipments} onChange={(v) => setNotifs((p) => ({ ...p, smsShipments: v }))} />
              </TabSection>
              <SaveBtn onClick={() => save({ notifs })} />
            </>
          )}

          {activeTab === 'preferences' && (
            <TabSection title="Display Preferences">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label style={labelSt}>Language</label>
                  <select style={{ ...inputSt, cursor: 'pointer' }} value={prefs.language} onChange={(e) => setPrefs((p) => ({ ...p, language: e.target.value }))}>
                    {LANGUAGES.map((l) => <option key={l}>{l}</option>)}
                  </select>
                </div>
                <div>
                  <label style={labelSt}>Timezone</label>
                  <select style={{ ...inputSt, cursor: 'pointer' }} value={prefs.timezone} onChange={(e) => setPrefs((p) => ({ ...p, timezone: e.target.value }))}>
                    {TIMEZONES.map((t) => <option key={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label style={labelSt}>Date Format</label>
                  <select style={{ ...inputSt, cursor: 'pointer' }} value={prefs.dateFormat} onChange={(e) => setPrefs((p) => ({ ...p, dateFormat: e.target.value }))}>
                    {['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'].map((f) => <option key={f}>{f}</option>)}
                  </select>
                </div>
              </div>
              <div style={{ marginTop: 20 }}>
                <SaveBtn onClick={() => save({ prefs })} />
              </div>
            </TabSection>
          )}

          {activeTab === 'sessions' && (
            <TabSection title="Active Sessions" description="Devices currently logged in to your account">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px', background: '#ECFDF5', border: '1.5px solid #A7F3D0', borderRadius: 10 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 9, background: '#D1FAE5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Monitor size={18} color="#10B981" /></div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13.5, fontWeight: 700, color: '#111827' }}>Current Session</div>
                    <div style={{ fontSize: 12, color: '#6B7280' }}>Browser · {new Date().toLocaleString()}</div>
                  </div>
                  <span style={{ fontSize: 11.5, fontWeight: 600, color: '#10B981', background: '#D1FAE5', borderRadius: 6, padding: '3px 10px' }}>Active</span>
                </div>
                <div style={{ padding: '16px', background: '#F9FAFB', borderRadius: 10, border: '1px solid #E5E7EB', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#6B7280' }}>
                  <Shield size={15} color="#9CA3AF" />
                  Session management and device history will be available after backend integration.
                </div>
              </div>
            </TabSection>
          )}
        </div>
      </div>
    </div>
  );
}
