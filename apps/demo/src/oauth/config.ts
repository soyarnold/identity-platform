/**
 * API origin for fetch/OAuth.
 * - Local default: http://localhost:8000
 * - Railway (same host): set VITE_API_URL="" at build so paths are "/oauth/..." etc.
 */
function apiOrigin(): string {
  if (import.meta.env.VITE_API_URL !== undefined) {
    return import.meta.env.VITE_API_URL;
  }
  return "http://localhost:8000";
}

const API_URL = apiOrigin();
const CLIENT_ID = import.meta.env.VITE_DEMO_CLIENT_ID ?? "demo-app";

function defaultRedirectUri(): string {
  // Shared-host deploy: callback lives under the Vite base (e.g. /demo/callback).
  if (typeof window !== "undefined" && import.meta.env.BASE_URL !== "/") {
    const base = import.meta.env.BASE_URL.replace(/\/$/, "");
    return `${window.location.origin}${base}/callback`;
  }
  return "http://localhost:5174/callback";
}

const REDIRECT_URI =
  import.meta.env.VITE_DEMO_REDIRECT_URI || defaultRedirectUri();

const AUTHORIZE_URL =
  import.meta.env.VITE_OAUTH_AUTHORIZE_URL || `${API_URL}/oauth/authorize`;
const TOKEN_URL =
  import.meta.env.VITE_OAUTH_TOKEN_URL || `${API_URL}/oauth/token`;
const USERINFO_URL =
  import.meta.env.VITE_OAUTH_USERINFO_URL || `${API_URL}/oauth/userinfo`;

export const config = {
  apiUrl: API_URL,
  clientId: CLIENT_ID,
  redirectUri: REDIRECT_URI,
  authorizeUrl: AUTHORIZE_URL,
  tokenUrl: TOKEN_URL,
  userinfoUrl: USERINFO_URL,
  scope: "openid profile email",
};
