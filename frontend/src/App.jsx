import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';

// Public pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import AuthCallback from './pages/AuthCallback';

// Protected dashboard pages
import Dashboard from './pages/Dashboard';
import DisruptionMonitor from './pages/DisruptionMonitor';
import RiskMap from './pages/RiskMap';
import KnowledgeGraph from './pages/KnowledgeGraph';
import Suppliers from './pages/Suppliers';
import Incidents from './pages/Incidents';
import Inventory from './pages/Inventory';
import Recommendations from './pages/Recommendations';
import Orchestration from './pages/Orchestration';
import Reports from './pages/Reports';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* ── Public routes (no auth required) ── */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/auth/callback" element={<AuthCallback />} />

          {/* ── Protected dashboard routes ── */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/disruption-monitor" element={<DisruptionMonitor />} />
              <Route path="/risk-map" element={<RiskMap />} />
              <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
              <Route path="/suppliers" element={<Suppliers />} />
              <Route path="/incidents" element={<Incidents />} />
              <Route path="/inventory" element={<Inventory />} />
              <Route path="/recommendations" element={<Recommendations />} />
              <Route path="/orchestration" element={<Orchestration />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Route>

          {/* ── Fallback ── */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
