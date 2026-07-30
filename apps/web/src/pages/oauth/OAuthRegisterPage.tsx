import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { ApiError } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import {
  consentPath,
  loginPath,
  parseAuthorizeParams,
} from "../../oauth/params";

export function OAuthRegisterPage() {
  const { user, register, loading } = useAuth();
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

  if (!loading && user) {
    return <Navigate to={consentPath(params)} replace />;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!params) return;
    setError(null);
    setBusy(true);
    try {
      await register(email, password);
      navigate(consentPath(params));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel narrow">
      <h1>Create account to continue</h1>
      <p className="muted">
        You&apos;ll authorize <strong>{params.client_id}</strong> after signing
        up.
      </p>
      <form className="stack" onSubmit={(e) => void onSubmit(e)}>
        <label>
          Email
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={busy}>
          Create account
        </button>
      </form>
      <p className="muted auth-switch">
        Already have an account? <Link to={loginPath(params)}>Sign in</Link>
      </p>
    </section>
  );
}
