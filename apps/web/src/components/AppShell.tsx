import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">
          Identity Platform
        </Link>
        {user ? (
          <nav className="nav">
            <NavLink to="/" end>
              Overview
            </NavLink>
            <NavLink to="/passkeys">Passkeys</NavLink>
            <NavLink to="/sessions">Sessions</NavLink>
            {user.is_admin ? (
              <>
                <NavLink to="/admin/users">Users</NavLink>
                <NavLink to="/admin/audit">Audit</NavLink>
                <NavLink to="/admin/clients">Clients</NavLink>
              </>
            ) : null}
            <button type="button" className="linkish" onClick={() => void logout()}>
              Sign out
            </button>
          </nav>
        ) : null}
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
