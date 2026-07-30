/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_DEMO_CLIENT_ID?: string;
  readonly VITE_DEMO_REDIRECT_URI?: string;
  readonly VITE_OAUTH_AUTHORIZE_URL?: string;
  readonly VITE_OAUTH_TOKEN_URL?: string;
  readonly VITE_OAUTH_USERINFO_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
