import { useEffect, useState } from "react";
import { listUsers, updateUser } from "../../api/admin";
import type { User } from "../../api/auth";
import { ApiError } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

export function AdminUsersPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const data = await listUsers();
      setUsers(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load users");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function toggleActive(u: User) {
    setBusyId(u.id);
    setError(null);
    try {
      await updateUser(u.id, { is_active: !u.is_active });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Update failed");
    } finally {
      setBusyId(null);
    }
  }

  async function toggleAdmin(u: User) {
    setBusyId(u.id);
    setError(null);
    try {
      await updateUser(u.id, { is_admin: !u.is_admin });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Update failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="panel">
      <h1>Users</h1>
      <p className="muted">
        {total} user{total === 1 ? "" : "s"}. Disable accounts or grant admin.
      </p>
      {error ? <p className="error">{error}</p> : null}
      <ul className="list">
        {users.map((u) => (
          <li key={u.id} className="list-item">
            <div>
              <strong>{u.email}</strong>
              <p className="muted small">
                <code>{u.id}</code>
                {" · "}
                {u.is_active ? "active" : "disabled"}
                {" · "}
                {u.is_admin ? "admin" : "user"}
              </p>
            </div>
            <div className="row">
              <button
                type="button"
                className="secondary"
                disabled={busyId === u.id || u.id === me?.id}
                onClick={() => void toggleActive(u)}
              >
                {u.is_active ? "Disable" : "Enable"}
              </button>
              <button
                type="button"
                className="secondary"
                disabled={busyId === u.id || u.id === me?.id}
                onClick={() => void toggleAdmin(u)}
              >
                {u.is_admin ? "Revoke admin" : "Make admin"}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
