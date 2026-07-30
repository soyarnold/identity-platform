import { useEffect, useState, type FormEvent } from "react";
import {
  createOAuthClient,
  deleteOAuthClient,
  listOAuthClients,
  type OAuthClient,
} from "../../api/admin";
import { ApiError } from "../../api/client";

export function AdminClientsPage() {
  const [clients, setClients] = useState<OAuthClient[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState("");
  const [clientId, setClientId] = useState("");
  const [redirectUri, setRedirectUri] = useState(
    "http://localhost:5174/callback",
  );

  async function load() {
    setError(null);
    try {
      const data = await listOAuthClients();
      setClients(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load clients");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createOAuthClient({
        name: name.trim(),
        client_id: clientId.trim(),
        redirect_uris: [redirectUri.trim()],
        is_confidential: false,
      });
      setName("");
      setClientId("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: string) {
    if (!window.confirm(`Delete OAuth client ${id}?`)) return;
    setError(null);
    try {
      await deleteOAuthClient(id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed");
    }
  }

  return (
    <section className="panel">
      <h1>OAuth clients</h1>
      <p className="muted">
        {total} client{total === 1 ? "" : "s"}. Public PKCE clients by default.
      </p>

      <form className="stack compact" onSubmit={(e) => void onCreate(e)}>
        <label>
          Name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </label>
        <label>
          Client ID
          <input
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            required
            minLength={3}
          />
        </label>
        <label>
          Redirect URI
          <input
            value={redirectUri}
            onChange={(e) => setRedirectUri(e.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={busy}>
          Create client
        </button>
      </form>

      {error ? <p className="error">{error}</p> : null}

      <ul className="list">
        {clients.map((c) => (
          <li key={c.client_id} className="list-item">
            <div>
              <strong>{c.name}</strong>
              <p className="muted small">
                <code>{c.client_id}</code>
                {" · "}
                {c.is_confidential ? "confidential" : "public"}
              </p>
              <p className="muted small break">
                {c.redirect_uris.join(", ")}
              </p>
            </div>
            <button
              type="button"
              className="danger"
              onClick={() => void onDelete(c.client_id)}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
