# Integrating your app (OAuth client)

This guide is for **third-party applications** that sign users in through Identity Platform. You do **not** need this repository. An Identity Platform **admin** registers your app and gives you a `client_id` and allowed redirect URIs.

Local Fieldkit (`apps/demo`) is a worked example of the same contract.

## What you receive from an admin

| Value | Notes |
|-------|--------|
| `client_id` | Public identifier (e.g. `my-app`) |
| Redirect URI(s) | Exact callback URL(s), e.g. `https://app.example.com/callback` |
| Client type | **Public** (PKCE, no secret) or **confidential** (server-side secret) |

You never receive database access, admin credentials, or this monorepo.

## Discovery

```http
GET {ISSUER}/.well-known/oauth-authorization-server
```

Local issuer: `http://localhost:8000/api`

Response includes `authorization_endpoint`, `token_endpoint`, `userinfo_endpoint`, and `code_challenge_methods_supported` (`S256`).

## Authorization Code + PKCE (public clients)

### 1. Generate PKCE

- `code_verifier`: high-entropy URL-safe string
- `code_challenge`: `BASE64URL(SHA256(code_verifier))` (no padding)
- `state`: random CSRF token (store with the verifier until callback)

### 2. Send the user to authorize

```http
GET {authorization_endpoint}
  ?client_id={client_id}
  &redirect_uri={exact_registered_uri}
  &response_type=code
  &code_challenge={challenge}
  &code_challenge_method=S256
  &state={state}
  &scope=openid%20profile%20email
```

Identity Platform hosts login/consent. After approval, the browser lands on:

```text
{redirect_uri}?code={authorization_code}&state={state}
```

On deny: `?error=access_denied&state=...`

### 3. Exchange the code

```http
POST {token_endpoint}
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code={authorization_code}
&redirect_uri={exact_registered_uri}
&client_id={client_id}
&code_verifier={code_verifier}
```

Confidential clients also send `client_secret`.

Response includes `access_token`, `token_type` (`Bearer`), `expires_in`, and optionally `refresh_token` (if `offline_access` was granted).

### 4. Call userinfo

```http
GET {userinfo_endpoint}
Authorization: Bearer {access_token}
```

Example body:

```json
{
  "sub": "…",
  "email": "user@example.com",
  "email_verified": true
}
```

## Refresh tokens

```http
POST {token_endpoint}
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token={refresh_token}
&client_id={client_id}
```

## Requirements checklist

- Redirect URI matches **exactly** what the admin registered (scheme, host, port, path)
- PKCE `S256` only (`plain` is not supported)
- `response_type=code` only
- Validate `state` on callback
- Treat authorization codes as one-time; do not reuse after a failed exchange

## Local smoke test

Against a local Identity Platform:

1. Admin (or seed) creates client `demo-app` → `http://localhost:5174/callback`
2. Run Fieldkit: `cd apps/demo && npm run dev`
3. Or follow `scripts/manual-phase04-oauth-curl.sh` for an API-only PKCE walkthrough

## Support

Ask your Identity Platform admin to adjust redirect URIs or rotate confidential secrets. Endpoints and scopes are defined by the deployment’s discovery document.
