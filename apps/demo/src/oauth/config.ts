/**
 * Fieldkit OAuth config.
 * Local (base `/`): API at VITE_API_URL or http://localhost:8000.
 * Shared host (base `/demo/`): same-origin relative `/oauth/...` paths.
 */
const sharedHost = import.meta.env.BASE_URL !== "/";

const API_URL = sharedHost
  ? ""
  : import.meta.env.VITE_API_URL || "http://localhost:8000";

function redirectUri(): string {
  if (sharedHost) {
    const base = import.meta.env.BASE_URL.replace(/\/$/, "");
    return `${window.location.origin}${base}/callback`;
  }
  return (
    import.meta.env.VITE_DEMO_REDIRECT_URI || "http://localhost:5174/callback"
  );
}

export const config = {
  apiUrl: API_URL,
  clientId: import.meta.env.VITE_DEMO_CLIENT_ID ?? "demo-app",
  get redirectUri() {
    return redirectUri();
  },
  authorizeUrl: `${API_URL}/oauth/authorize`,
  tokenUrl: `${API_URL}/oauth/token`,
  userinfoUrl: `${API_URL}/oauth/userinfo`,
  scope: "openid profile email",
};
