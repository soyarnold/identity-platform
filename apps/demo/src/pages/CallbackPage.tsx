import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { exchangeCode, fetchUserInfo } from "../oauth/client";
import {
  clearPkce,
  loadProfile,
  peekPkce,
  saveSession,
  type UserInfo,
} from "../oauth/pkce";

// Share one exchange across React StrictMode double-invoke (same auth code).
const exchanges = new Map<string, Promise<UserInfo>>();

function completeSignIn(code: string, state: string): Promise<UserInfo> {
  const existing = exchanges.get(code);
  if (existing) return existing;

  const promise = (async () => {
    const pkce = peekPkce();
    if (!pkce) {
      throw new Error(
        "Missing PKCE verifier. Start again from home (sessionStorage cleared).",
      );
    }
    if (state !== pkce.state) {
      throw new Error("State mismatch — possible CSRF. Start again from home.");
    }
    const tokens = await exchangeCode(code, pkce.verifier);
    const profile = await fetchUserInfo(tokens.access_token);
    clearPkce();
    saveSession(tokens, profile);
    return profile;
  })().finally(() => {
    exchanges.delete(code);
  });

  exchanges.set(code, promise);
  return promise;
}

export function CallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    async function finish() {
      const oauthError = searchParams.get("error");
      if (oauthError) {
        if (alive) {
          setError(
            oauthError === "access_denied"
              ? "Access was denied on the consent screen."
              : `Authorization failed: ${oauthError}`,
          );
        }
        return;
      }

      const code = searchParams.get("code");
      const state = searchParams.get("state");
      if (!code || !state) {
        if (alive) {
          setError("Missing code or state. Start again from home.");
        }
        return;
      }

      try {
        await completeSignIn(code, state);
        if (alive) navigate("/", { replace: true });
      } catch (err) {
        // Sibling StrictMode run may have already finished successfully.
        if (loadProfile()) {
          if (alive) navigate("/", { replace: true });
          return;
        }
        if (alive) {
          setError(
            err instanceof Error ? err.message : "Token exchange failed",
          );
        }
      }
    }

    void finish();
    return () => {
      alive = false;
    };
  }, [searchParams, navigate]);

  if (error) {
    return (
      <section className="panel">
        <h2>Sign-in failed</h2>
        <p className="error">{error}</p>
        <Link className="button" to="/">
          Back to Fieldkit
        </Link>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>Completing sign-in…</h2>
      <p className="muted">Exchanging authorization code for tokens.</p>
    </section>
  );
}
