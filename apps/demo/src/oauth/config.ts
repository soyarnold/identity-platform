const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const CLIENT_ID = import.meta.env.VITE_DEMO_CLIENT_ID ?? "demo-app";
const REDIRECT_URI =
  import.meta.env.VITE_DEMO_REDIRECT_URI ?? "http://localhost:5174/callback";
const AUTHORIZE_URL =
  import.meta.env.VITE_OAUTH_AUTHORIZE_URL ?? `${API_URL}/oauth/authorize`;
const TOKEN_URL =
  import.meta.env.VITE_OAUTH_TOKEN_URL ?? `${API_URL}/oauth/token`;
const USERINFO_URL =
  import.meta.env.VITE_OAUTH_USERINFO_URL ?? `${API_URL}/oauth/userinfo`;

export const config = {
  apiUrl: API_URL,
  clientId: CLIENT_ID,
  redirectUri: REDIRECT_URI,
  authorizeUrl: AUTHORIZE_URL,
  tokenUrl: TOKEN_URL,
  userinfoUrl: USERINFO_URL,
  scope: "openid profile email",
};
