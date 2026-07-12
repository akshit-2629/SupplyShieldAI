import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { MapPin, X, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { severityColor } from '../lib/utils';

const typeIcon = {
  GEOPOLITICAL:   '🏛️',
  NATURAL_DISASTER:'🌊',
  LABOR:          '✊',
  FINANCIAL:      '💰',
  CYBER:          '💻',
  PANDEMIC:       '🦠',
  REGULATORY:     '📋',
};

// Approximate country centroids (ISO-2 → [lat, lng])
const countryCentroids = {
  TW:[23.7,121.0], KR:[35.9,127.8], JP:[36.2,138.3], CN:[35.9,104.2],
  US:[37.1,-95.7], DE:[51.2,10.5],  FR:[46.2,2.2],   GB:[54.4,-3.4],
  RU:[61.5,105.3], UA:[48.4,31.2],  IN:[20.6,78.9],   ID:[-5.3,119.2],
  TH:[15.9,100.9], VN:[14.1,108.3], MY:[4.2,108.0],   SG:[1.4,103.8],
  AU:[-25.3,133.8],NL:[52.1,5.3],   EG:[26.8,30.8],   TR:[38.9,35.2],
};

function getLatLng(countries) {
  if (!countries || countries.length === 0) return [25, 10];
  const code = countries[0];
  return countryCentroids[code] || [25, 10];
}

export default function RiskMap() {
  const [selectedEvent, setSelectedEvent]     = useState(null);
  const [MapComponents,  setMapComponents]    = useState(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['risk-map-events'],
    queryFn:  () => api.get('/risk/assessments'),
    staleTime: 60_000,
  });

  const assessments = Array.isArray(data)
    ? data
    : Array.isArray(data?.assessments)
    ? data.assessments
    : [];

  // Only HIGH and CRITICAL on the map
  const mapEvents = assessments.filter(a => ['HIGH', 'CRITICAL'].includes(a.risk_level));

  useEffect(() => {
    Promise.all([import('react-leaflet'), import('leaflet')]).then(([rl, L]) => {
      delete L.default.Icon.Default.prototype._getIconUrl;
      L.default.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      });
      setMapComponents({ ...rl, L: L.default });
    });
  }, []);

  const getMarkerColor = (level) => {
    const m = { CRITICAL: '#DC2626', HIGH: '#D97706', MEDIUM: '#CA8A04', LOW: '#059669' };
    return m[level] || '#6B7280';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, height: 'calc(100vh - 110px)' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexShrink: 0 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginBottom: 4 }}>Global Risk Map</h1>
          <p style={{ fontSize: 13.5, color: '#9CA3AF' }}>Live visualization of HIGH + CRITICAL supply chain risk events from AI Risk Agent</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(s => {
            const sc = severityColor(s.toLowerCase());
            return (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 5, background: 'white', border: '1px solid #E5E7EB', borderRadius: 7, padding: '5px 10px', fontSize: 12 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: sc.dot }} />
                <span style={{ color: '#6B7280', fontWeight: 500 }}>{s}</span>
              </div>
            );
          })}
          <button onClick={() => refetch()} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 8, padding: '7px 12px', fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>
            <RefreshCw size={13} />
          </button>
        </div>
      </motion.div>

      {/* Map + Side Panel */}
      <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0 }}>
        {/* Map */}
        <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }}
          className="card" style={{ flex: 1, overflow: 'hidden', position: 'relative' }}
        >
          {!MapComponents || isLoading ? (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F9FAFB' }}>
              <div style={{ textAlign: 'center', color: '#9CA3AF' }}>
                <div className="skeleton" style={{ width: 48, height: 48, borderRadius: '50%', margin: '0 auto 12px' }} />
                <div style={{ fontSize: 13 }}>Loading risk map…</div>
              </div>
            </div>
          ) : (() => {
            const { MapContainer, TileLayer, CircleMarker, Popup } = MapComponents;
            return (
              <MapContainer center={[25, 10]} zoom={2} style={{ height: '100%', width: '100%', borderRadius: 8 }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {mapEvents.map((d, idx) => {
                  const [lat, lng] = getLatLng(d.countries);
                  return (
                    <CircleMarker
                      key={d.assessment_id || idx}
                      center={[lat, lng]}
                      radius={d.risk_level === 'CRITICAL' ? 16 : 13}
                      pathOptions={{ color: getMarkerColor(d.risk_level), fillColor: getMarkerColor(d.risk_level), fillOpacity: 0.25, weight: 2 }}
                      eventHandlers={{ click: () => setSelectedEvent(d) }}
                    >
                      <Popup>
                        <div style={{ fontFamily: 'Inter, sans-serif', minWidth: 200 }}>
                          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4 }}>{d.title}</div>
                          <div style={{ fontSize: 12, color: '#6B7280', marginBottom: 8 }}>{(d.countries || []).join(', ')}</div>
                          <div style={{ display: 'flex', gap: 6 }}>
                            <span style={{ background: severityColor((d.risk_level || '').toLowerCase()).bg, color: severityColor((d.risk_level || '').toLowerCase()).text, fontSize: 10, padding: '2px 7px', borderRadius: 8, fontWeight: 700 }}>{d.risk_level}</span>
                            <span style={{ fontSize: 11, color: '#9CA3AF' }}>Score: {(d.risk_score || 0).toFixed(0)}</span>
                          </div>
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}
              </MapContainer>
            );
          })()}
        </motion.div>

        {/* Event List */}
        <motion.div initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
          className="card" style={{ width: 300, display: 'flex', flexDirection: 'column', overflow: 'hidden', flexShrink: 0 }}
        >
          <div style={{ padding: '14px 16px', borderBottom: '1px solid #F3F4F6', fontSize: 13, fontWeight: 700, color: '#111827' }}>
            Active Events ({isLoading ? '…' : mapEvents.length})
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
            {mapEvents.map(d => {
              const sc = severityColor((d.risk_level || '').toLowerCase());
              const isSelected = selectedEvent?.assessment_id === d.assessment_id;
              return (
                <button key={d.assessment_id} onClick={() => setSelectedEvent(isSelected ? null : d)}
                  style={{ width: '100%', display: 'flex', gap: 10, padding: '10px', borderRadius: 8, border: `1px solid ${isSelected ? '#BFDBFE' : 'transparent'}`, background: isSelected ? '#EFF6FF' : 'transparent', cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s', marginBottom: 4 }}
                  onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = '#FAFAFA'; }}
                  onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
                >
                  <div style={{ fontSize: 18, flexShrink: 0, marginTop: 1 }}>{typeIcon[d.event_type] || '⚠️'}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#111827', marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.title}</div>
                    <div style={{ fontSize: 11, color: '#9CA3AF', marginBottom: 5 }}>{(d.countries || []).slice(0, 2).join(', ') || 'Global'}</div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <span style={{ background: sc.bg, color: sc.text, fontSize: 10, fontWeight: 700, padding: '1px 6px', borderRadius: 8, textTransform: 'uppercase' }}>{d.risk_level}</span>
                      <span style={{ fontSize: 10, color: '#9CA3AF' }}>{(d.risk_score || 0).toFixed(0)}/100</span>
                    </div>
                  </div>
                </button>
              );
            })}
            {!isLoading && mapEvents.length === 0 && (
              <div style={{ padding: 16, textAlign: 'center', color: '#9CA3AF', fontSize: 13 }}>
                No HIGH/CRITICAL events found. Run the AI workflow first.
              </div>
            )}
          </div>

          {/* Detail panel */}
          {selectedEvent && (
            <div style={{ borderTop: '1px solid #F3F4F6', padding: 14, background: '#FAFBFF' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#111827' }}>{selectedEvent.title}</div>
                <button onClick={() => setSelectedEvent(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9CA3AF' }}><X size={14} /></button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {[
                  { label: 'Risk Score',  value: (selectedEvent.risk_score || 0).toFixed(0) },
                  { label: 'Confidence', value: selectedEvent.confidence_label || '—' },
                  { label: 'Trajectory', value: selectedEvent.trajectory || '—' },
                  { label: 'Industries', value: (selectedEvent.industries || []).length || '—' },
                ].map(item => (
                  <div key={item.label} style={{ background: 'white', border: '1px solid #E5E7EB', borderRadius: 6, padding: '8px 10px', textAlign: 'center' }}>
                    <div style={{ fontSize: 10, color: '#9CA3AF' }}>{item.label}</div>
                    <div style={{ fontSize: 15, fontWeight: 800, color: '#111827' }}>{item.value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
