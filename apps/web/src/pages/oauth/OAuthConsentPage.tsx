import { useState } from "react";
import { Navigate, useSearchParams } from "react-router-dom";
import { submitConsent } from "../../api/oauth";
import { ApiError } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { loginPath, parseAuthorizeParams } from "../../oauth/params";

export function OAuthConsentPage() {
  const { user, loading } = useAuth();
  const [searchParams] = useSearchParams();
  const params = parseAuthorizeParams(searchParams);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!params) {
    return (
      <section className="panel narrow">
        <h1>Invalid request</h1>
        <p className="muted">
          Missing OAuth authorize parameters. Start again from the application
          that sent you here.
        </p>
      </section>
    );
  }

  if (!loading && !user) {
    return <Navigate to={loginPath(params)} replace />;
  }

  if (loading || !user) {
    return <p className="muted">Loading…</p>;
  }

  async function finish(approve: boolean) {
    if (!params) return;
    setError(null);
    setBusy(true);
    try {
      const { redirect_to } = await submitConsent(params, approve);
      // Leave Identity Platform and return to the third-party callback.
      window.location.assign(redirect_to);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Consent failed");
      setBusy(false);
    }
  }

  const scopes = (params.scope ?? "openid profile email")
    .split(/\s+/)
    .filter(Boolean);

  return (
    <section className="panel narrow">
      <h1>Authorize application</h1>
      <p className="muted">
        Signed in as <strong>{user.email}</strong>
      </p>

      <dl className="meta">
        <div>
          <dt>Application</dt>
          <dd>
            <code>{params.client_id}</code>
          </dd>
        </div>
        <div>
          <dt>Redirect URI</dt>
          <dd className="break">
            <code>{params.redirect_uri}</code>
          </dd>
        </div>
        <div>
          <dt>Permissions</dt>
          <dd>
            <ul className="scope-list">
              {scopes.map((s) => (
                <li key={s}>
                  <code>{s}</code>
                </li>
              ))}
            </ul>
          </dd>
        </div>
      </dl>

      {error ? <p className="error">{error}</p> : null}

      <div className="row">
        <button type="button" disabled={busy} onClick={() => void finish(true)}>
          Allow
        </button>
        <button
          type="button"
          className="secondary"
          disabled={busy}
          onClick={() => void finish(false)}
        >
          Deny
        </button>
      </div>
    </section>
  );
}
