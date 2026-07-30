/** Authorize query params forwarded by GET /oauth/authorize → hosted UI. */

export type AuthorizeParams = {
  client_id: string;
  redirect_uri: string;
  response_type: string;
  code_challenge: string;
  code_challenge_method: string;
  state: string | null;
  scope: string | null;
};

const REQUIRED = [
  "client_id",
  "redirect_uri",
  "response_type",
  "code_challenge",
] as const;

export function parseAuthorizeParams(
  searchParams: URLSearchParams,
): AuthorizeParams | null {
  for (const key of REQUIRED) {
    if (!searchParams.get(key)) {
      return null;
    }
  }
  return {
    client_id: searchParams.get("client_id")!,
    redirect_uri: searchParams.get("redirect_uri")!,
    response_type: searchParams.get("response_type")!,
    code_challenge: searchParams.get("code_challenge")!,
    code_challenge_method: searchParams.get("code_challenge_method") || "S256",
    state: searchParams.get("state"),
    scope: searchParams.get("scope"),
  };
}

/** Build ?query=… for /oauth/login|register|consent so the flow can resume. */
export function authorizeSearch(params: AuthorizeParams): string {
  const q = new URLSearchParams();
  q.set("client_id", params.client_id);
  q.set("redirect_uri", params.redirect_uri);
  q.set("response_type", params.response_type);
  q.set("code_challenge", params.code_challenge);
  q.set("code_challenge_method", params.code_challenge_method);
  if (params.state) q.set("state", params.state);
  if (params.scope) q.set("scope", params.scope);
  return `?${q.toString()}`;
}

export function consentPath(params: AuthorizeParams): string {
  return `/oauth/consent${authorizeSearch(params)}`;
}

export function loginPath(params: AuthorizeParams): string {
  return `/oauth/login${authorizeSearch(params)}`;
}

export function registerPath(params: AuthorizeParams): string {
  return `/oauth/register${authorizeSearch(params)}`;
}
