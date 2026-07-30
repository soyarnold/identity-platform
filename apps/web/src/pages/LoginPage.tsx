import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import {
  startAuthentication,
} from "@simplewebauthn/browser";
import { webauthnLoginOptions, webauthnLoginVerify } from "../api/auth";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { user, login, setUser } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) {
    return <Navigate to="/" replace />;
  }

  async function onPasswordSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  async function onPasskeyLogin() {
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
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Passkey login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel narrow">
      <h1>Sign in</h1>
      <p className="muted">Email and password, or a registered passkey.</p>
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
        No account? <Link to="/register">Create one</Link>
      </p>
    </section>
  );
}
