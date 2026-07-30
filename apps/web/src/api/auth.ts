import type {
  AuthenticationResponseJSON,
  PublicKeyCredentialCreationOptionsJSON,
  PublicKeyCredentialRequestOptionsJSON,
  RegistrationResponseJSON,
} from "@simplewebauthn/browser";
import { api } from "./client";

export type User = {
  id: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
};

export type Session = {
  id: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string;
  expires_at: string;
  is_current: boolean;
};

export type Passkey = {
  id: string;
  device_name: string | null;
  transports: string[] | null;
  created_at: string;
  last_used_at: string | null;
  sign_count: number;
};

export function register(email: string, password: string) {
  return api<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function login(email: string, password: string) {
  return api<User>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function logout() {
  return api<{ message: string }>("/auth/logout", { method: "POST" });
}

export function me() {
  return api<User>("/auth/me");
}

export function listSessions() {
  return api<Session[]>("/me/sessions");
}

export function revokeSession(sessionId: string) {
  return api<{ message: string }>(`/me/sessions/${sessionId}/revoke`, {
    method: "POST",
  });
}

export function listPasskeys() {
  return api<Passkey[]>("/me/passkeys");
}

export function renamePasskey(id: string, device_name: string) {
  return api<Passkey>(`/me/passkeys/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ device_name }),
  });
}

export function deletePasskey(id: string) {
  return api<{ message: string }>(`/me/passkeys/${id}`, { method: "DELETE" });
}

export function webauthnRegisterOptions() {
  return api<{ options: PublicKeyCredentialCreationOptionsJSON }>(
    "/webauthn/register/options",
    { method: "POST" },
  );
}

export function webauthnRegisterVerify(
  credential: RegistrationResponseJSON,
  device_name?: string,
) {
  return api<Passkey>("/webauthn/register/verify", {
    method: "POST",
    body: JSON.stringify({ credential, device_name }),
  });
}

export function webauthnLoginOptions(email: string) {
  return api<{ options: PublicKeyCredentialRequestOptionsJSON }>(
    "/webauthn/login/options",
    {
      method: "POST",
      body: JSON.stringify({ email }),
    },
  );
}

export function webauthnLoginVerify(
  email: string,
  credential: AuthenticationResponseJSON,
) {
  return api<User>("/webauthn/login/verify", {
    method: "POST",
    body: JSON.stringify({ email, credential }),
  });
}
