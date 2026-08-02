import { useState } from "react";
import { Link } from "react-router-dom";
import { startLogin } from "../oauth/client";
import { clearSession, loadProfile } from "../oauth/pkce";
import { config } from "../oauth/config";

export function HomePage() {
  const [profile, setProfile] = useState(() => loadProfile());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSignIn() {
    setError(null);
    setBusy(true);
    try {
      await startLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start login");
      setBusy(false);
    }
  }

  function onSignOut() {
    clearSession();
    setProfile(null);
  }

  if (profile) {
    return (
      <section className="panel">
        <h2>Signed in to Fieldkit</h2>
        <p className="muted">
          Tokens came from Identity Platform via OAuth 2.0 + PKCE.
        </p>
        <dl className="meta">
          <div>
            <dt>Email</dt>
            <dd>{profile.email}</dd>
          </div>
          <div>
            <dt>Subject</dt>
            <dd>
              <code>{profile.sub}</code>
            </dd>
          </div>
          <div>
            <dt>Email verified</dt>
            <dd>{profile.email_verified ? "Yes" : "No"}</dd>
          </div>
        </dl>
        <div className="row" style={{ marginTop: "1.25rem" }}>
          <button type="button" className="secondary" onClick={onSignOut}>
            Sign out
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="hero">
      <h1>Fieldkit</h1>
      <p className="lede">
        A sample third-party app that signs in through Identity Platform — no
        password form of its own.
      </p>
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="button" disabled={busy} onClick={() => void onSignIn()}>
          Sign in with Identity Platform
        </button>
      </div>
      <p className="hint">
        Needs API + hosted Identity UI (local :8000 / :5173, or same host in
        production) and OAuth client <code>{config.clientId}</code> with redirect{" "}
        <code>{config.redirectUri}</code>. Create via seed, admin Clients, or{" "}
        <code>POST /api/oauth/dev/clients</code>.{" "}
        <Link to="/callback">Callback</Link> handles the code exchange.
      </p>
    </section>
  );
}
