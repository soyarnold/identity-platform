/** PKCE S256 helpers for a public OAuth client (browser-only). */

function base64Url(bytes: ArrayBuffer | Uint8Array): string {
  const view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let binary = "";
  for (const b of view) {
    binary += String.fromCharCode(b);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function randomUrlSafe(byteLength = 32): string {
  const bytes = crypto.getRandomValues(new Uint8Array(byteLength));
  return base64Url(bytes);
}

export async function pkceChallengeS256(verifier: string): Promise<string> {
  const data = new TextEncoder().encode(verifier);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return base64Url(digest);
}

const VERIFIER_KEY = "fieldkit_pkce_verifier";
const STATE_KEY = "fieldkit_oauth_state";
const TOKEN_KEY = "fieldkit_tokens";
const PROFILE_KEY = "fieldkit_profile";

export type TokenBundle = {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string | null;
  scope?: string | null;
};

export type UserInfo = {
  sub: string;
  email: string;
  email_verified: boolean;
};

export function storePkce(verifier: string, state: string): void {
  sessionStorage.setItem(VERIFIER_KEY, verifier);
  sessionStorage.setItem(STATE_KEY, state);
}

export function peekPkce(): { verifier: string; state: string } | null {
  const verifier = sessionStorage.getItem(VERIFIER_KEY);
  const state = sessionStorage.getItem(STATE_KEY);
  if (!verifier || !state) return null;
  return { verifier, state };
}

export function clearPkce(): void {
  sessionStorage.removeItem(VERIFIER_KEY);
  sessionStorage.removeItem(STATE_KEY);
}

export function takePkce(): { verifier: string; state: string } | null {
  const pkce = peekPkce();
  clearPkce();
  return pkce;
}

export function saveSession(tokens: TokenBundle, profile: UserInfo): void {
  sessionStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  sessionStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

export function loadProfile(): UserInfo | null {
  const raw = sessionStorage.getItem(PROFILE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserInfo;
  } catch {
    return null;
  }
}

export function loadTokens(): TokenBundle | null {
  const raw = sessionStorage.getItem(TOKEN_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as TokenBundle;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(PROFILE_KEY);
  sessionStorage.removeItem(VERIFIER_KEY);
  sessionStorage.removeItem(STATE_KEY);
}
