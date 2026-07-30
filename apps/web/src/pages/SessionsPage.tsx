import { useCallback, useEffect, useState } from "react";
import { listSessions, revokeSession, type Session } from "../api/auth";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function SessionsPage() {
  const { refresh } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setSessions(await listSessions());
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to load sessions",
      );
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onRevoke(session: Session) {
    const msg = session.is_current
      ? "Revoke this session? You will be signed out."
      : "Revoke this session?";
    if (!confirm(msg)) return;
    setError(null);
    try {
      await revokeSession(session.id);
      if (session.is_current) {
        await refresh();
        return;
      }
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Revoke failed");
    }
  }

  return (
    <section className="panel">
      <h1>Sessions</h1>
      <p className="muted">
        Active sign-ins for your account. Revoke any you do not recognize.
      </p>
      {error ? <p className="error">{error}</p> : null}
      {sessions.length === 0 ? (
        <p className="muted">No active sessions.</p>
      ) : (
        <ul className="list">
          {sessions.map((s) => (
            <li key={s.id} className="list-item">
              <div>
                <strong>
                  {s.is_current ? "This device" : "Other session"}
                </strong>
                <div className="muted small">
                  {s.user_agent ?? "Unknown client"}
                  {s.ip_address ? ` · ${s.ip_address}` : ""}
                </div>
                <div className="muted small">
                  Started {new Date(s.created_at).toLocaleString()} · Expires{" "}
                  {new Date(s.expires_at).toLocaleString()}
                </div>
              </div>
              <button
                type="button"
                className="danger"
                onClick={() => void onRevoke(s)}
              >
                Revoke
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
