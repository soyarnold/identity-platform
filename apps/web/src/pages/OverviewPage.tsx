import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function OverviewPage() {
  const { user } = useAuth();

  return (
    <section className="panel">
      <h1>Overview</h1>
      <p className="muted">Signed in as {user?.email}</p>
      <dl className="meta">
        <div>
          <dt>User ID</dt>
          <dd>
            <code>{user?.id}</code>
          </dd>
        </div>
        <div>
          <dt>Admin</dt>
          <dd>{user?.is_admin ? "Yes" : "No"}</dd>
        </div>
        <div>
          <dt>Active</dt>
          <dd>{user?.is_active ? "Yes" : "No"}</dd>
        </div>
      </dl>
      <div className="row">
        <Link className="button" to="/passkeys">
          Manage passkeys
        </Link>
        <Link className="button secondary" to="/sessions">
          View sessions
        </Link>
        {user?.is_admin ? (
          <Link className="button secondary" to="/admin/users">
            Admin panel
          </Link>
        ) : null}
      </div>
    </section>
  );
}
