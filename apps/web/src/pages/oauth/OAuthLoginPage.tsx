import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { startAuthentication } from "@simplewebauthn/browser";
import { webauthnLoginOptions, webauthnLoginVerify } from "../../api/auth";
import { ApiError } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import {
  consentPath,
  parseAuthorizeParams,
  registerPath,
} from "../../oauth/params";

export function OAuthLoginPage() {
  const { user, login, setUser, loading } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const params = parseAuthorizeParams(searchParams);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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

  // Already signed in → continue to consent with the same query string.
  if (!loading && user) {
    return <Navigate to={consentPath(params)} replace />;
  }

  async function onPasswordSubmit(e: FormEvent) {
    e.preventDefault();
    if (!params) return;
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate(consentPath(params));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  async function onPasskeyLogin() {
    if (!params) return;
    setError(null);
    if (!email.trim()) {
      setError("Enter your email first, then use passkey sign-in.");
      return;
    }
    setBusy(true);
    try {
      const { options } = await webauthnLoginOptions(email.trim());
      const credential = await startAuthentication({ optionsJSON: options });
      const u = await webauthnLoginVerify(email.trim(), credential);
      setUser(u);
      navigate(consentPath(params));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Passkey login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel narrow">
      <h1>Sign in to continue</h1>
      <p className="muted">
        Sign in to authorize <strong>{params.client_id}</strong>.
      </p>
      <form className="stack" onSubmit={(e) => void onPasswordSubmit(e)}>
        <label>
          Email
          <input
            type="email"
            autoComplete="username webauthn"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={busy}>
          Sign in with password
        </button>
        <button
          type="button"
          className="secondary"
          disabled={busy}
          onClick={() => void onPasskeyLogin()}
        >
          Sign in with passkey
        </button>
      </form>
      <p className="muted auth-switch">
        No account?{" "}
        <Link to={registerPath(params)}>Create one</Link>
      </p>
    </section>
  );
}
