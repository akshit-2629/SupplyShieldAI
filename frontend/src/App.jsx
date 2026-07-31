import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { SupplierAuthProvider } from './context/SupplierAuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import SupplierProtectedRoute from './components/auth/SupplierProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';
import SupplierLayout from './layouts/SupplierLayout';

// ── Public pages ──────────────────────────────────────────────────────────
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import AuthCallback from './pages/AuthCallback';
import RoleSelect from './pages/RoleSelect';

// ── Supplier auth pages ───────────────────────────────────────────────────
import SupplierLogin from './pages/supplier/SupplierLogin';
import SupplierRegister from './pages/supplier/SupplierRegister';

// ── Supplier portal pages ─────────────────────────────────────────────────
import SupplierDashboard from './pages/supplier/SupplierDashboard';
import CompanyProfile from './pages/supplier/CompanyProfile';
import ProductionCapacity from './pages/supplier/ProductionCapacity';
import InventoryManagement from './pages/supplier/InventoryManagement';
import LeadTimeManagement from './pages/supplier/LeadTimeManagement';
import ShipmentManagement from './pages/supplier/ShipmentManagement';
import IncidentReporting from './pages/supplier/IncidentReporting';
import CapacityForecast from './pages/supplier/CapacityForecast';
import PerformanceMetrics from './pages/supplier/PerformanceMetrics';
import SupplierNotifications from './pages/supplier/SupplierNotifications';
import SupportCenter from './pages/supplier/SupportCenter';
import SupplierSettings from './pages/supplier/SupplierSettings';
// ── Module C pages ────────────────────────────────────────────────────────
import SupplierSetup from './pages/supplier/SupplierSetup';
import QualityManagement from './pages/supplier/QualityManagement';
import DocumentCenter from './pages/supplier/DocumentCenter';

// ── Admin dashboard pages (unchanged) ────────────────────────────────────
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
import Setup from './pages/Setup';
import SupplierManagement from './pages/SupplierManagement'; // Module B
import BusinessManagement from './pages/BusinessManagement';

import { ErrorBoundary } from './components/common/ErrorBoundary';

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <SupplierAuthProvider>
            <Routes>
            {/* ── Public routes ── */}
            <Route path="/" element={<Landing />} />
            <Route path="/role-select" element={<RoleSelect />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/auth/callback" element={<AuthCallback />} />

            {/* ── Supplier auth (public) ── */}
            <Route path="/supplier/login" element={<SupplierLogin />} />
            <Route path="/supplier/register" element={<SupplierRegister />} />

            {/* ── Supplier portal (protected) ── */}
            <Route element={<SupplierProtectedRoute />}>
              <Route element={<SupplierLayout />}>
                <Route path="/supplier/dashboard"     element={<SupplierDashboard />} />
                <Route path="/supplier/profile"       element={<CompanyProfile />} />
                <Route path="/supplier/production"    element={<ProductionCapacity />} />
                <Route path="/supplier/inventory"     element={<InventoryManagement />} />
                <Route path="/supplier/lead-time"     element={<LeadTimeManagement />} />
                <Route path="/supplier/shipments"     element={<ShipmentManagement />} />
                <Route path="/supplier/incidents"     element={<IncidentReporting />} />
                <Route path="/supplier/forecast"      element={<CapacityForecast />} />
                <Route path="/supplier/metrics"       element={<PerformanceMetrics />} />
                <Route path="/supplier/notifications" element={<SupplierNotifications />} />
                <Route path="/supplier/support"       element={<SupportCenter />} />
                <Route path="/supplier/settings"      element={<SupplierSettings />} />
                {/* Module C routes */}
                <Route path="/supplier/setup"         element={<SupplierSetup />} />
                <Route path="/supplier/quality"        element={<QualityManagement />} />
                <Route path="/supplier/documents"      element={<DocumentCenter />} />
                {/* Redirect /supplier → /supplier/dashboard */}
                <Route path="/supplier" element={<Navigate to="/supplier/dashboard" replace />} />
              </Route>
            </Route>

            {/* ── Manufacturer Setup Wizard (protected, full-screen — no layout wrapper) ── */}
            <Route element={<ProtectedRoute />}>
              <Route path="/setup" element={<Setup />} />
            </Route>

            {/* ── Admin dashboard routes ── */}
            <Route element={<ProtectedRoute />}>
              <Route element={<DashboardLayout />}>
                <Route path="/dashboard"           element={<Dashboard />} />
                <Route path="/business-management" element={<BusinessManagement />} />
                <Route path="/disruption-monitor"  element={<DisruptionMonitor />} />
                <Route path="/risk-map"            element={<RiskMap />} />
                <Route path="/knowledge-graph"     element={<KnowledgeGraph />} />
                <Route path="/suppliers"           element={<Suppliers />} />
                <Route path="/incidents"           element={<Incidents />} />
                <Route path="/inventory"           element={<Inventory />} />
                <Route path="/recommendations"     element={<Recommendations />} />
                <Route path="/orchestration"       element={<Orchestration />} />
                <Route path="/reports"             element={<Reports />} />
                <Route path="/alerts"              element={<Alerts />} />
                <Route path="/settings"            element={<Settings />} />
                <Route path="/supplier-management" element={<SupplierManagement />} />
              </Route>
            </Route>

            {/* ── Fallback ── */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </SupplierAuthProvider>
      </AuthProvider>
    </BrowserRouter>
    </ErrorBoundary>
  );
}
