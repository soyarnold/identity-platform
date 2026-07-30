import { config } from "./config";
import {
  pkceChallengeS256,
  randomUrlSafe,
  storePkce,
  type TokenBundle,
  type UserInfo,
} from "./pkce";

export async function startLogin(): Promise<void> {
  // Public-client PKCE: keep verifier in sessionStorage until /callback.
  const verifier = randomUrlSafe(64);
  const challenge = await pkceChallengeS256(verifier);
  const state = randomUrlSafe(16);
  storePkce(verifier, state);

  const params = new URLSearchParams({
    client_id: config.clientId,
    redirect_uri: config.redirectUri,
    response_type: "code",
    code_challenge: challenge,
    code_challenge_method: "S256",
    state,
    scope: config.scope,
  });

  window.location.assign(`${config.authorizeUrl}?${params.toString()}`);
}

export async function exchangeCode(
  code: string,
  codeVerifier: string,
): Promise<TokenBundle> {
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    code,
    redirect_uri: config.redirectUri,
    client_id: config.clientId,
    code_verifier: codeVerifier,
  });

  const res = await fetch(config.tokenUrl, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Token exchange failed (${res.status})`);
  }

  return (await res.json()) as TokenBundle;
}

export async function fetchUserInfo(accessToken: string): Promise<UserInfo> {
  const res = await fetch(config.userinfoUrl, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Userinfo failed (${res.status})`);
  }

  return (await res.json()) as UserInfo;
}
