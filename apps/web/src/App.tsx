import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { AdminRoute } from "./components/AdminRoute";
import { AppShell } from "./components/AppShell";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { OverviewPage } from "./pages/OverviewPage";
import { PasskeysPage } from "./pages/PasskeysPage";
import { RegisterPage } from "./pages/RegisterPage";
import { SessionsPage } from "./pages/SessionsPage";
import { AdminAuditPage } from "./pages/admin/AdminAuditPage";
import { AdminClientsPage } from "./pages/admin/AdminClientsPage";
import { AdminUsersPage } from "./pages/admin/AdminUsersPage";
import { OAuthConsentPage } from "./pages/oauth/OAuthConsentPage";
import { OAuthLoginPage } from "./pages/oauth/OAuthLoginPage";
import { OAuthRegisterPage } from "./pages/oauth/OAuthRegisterPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            {/* Hosted OAuth UI — params preserved from GET /oauth/authorize */}
            <Route path="/oauth/login" element={<OAuthLoginPage />} />
            <Route path="/oauth/register" element={<OAuthRegisterPage />} />
            <Route path="/oauth/consent" element={<OAuthConsentPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<OverviewPage />} />
              <Route path="/passkeys" element={<PasskeysPage />} />
              <Route path="/sessions" element={<SessionsPage />} />
            </Route>
            <Route element={<AdminRoute />}>
              <Route path="/admin/users" element={<AdminUsersPage />} />
              <Route path="/admin/audit" element={<AdminAuditPage />} />
              <Route path="/admin/clients" element={<AdminClientsPage />} />
              <Route
                path="/admin"
                element={<Navigate to="/admin/users" replace />}
              />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
