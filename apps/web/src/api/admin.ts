import { api } from "./client";
import type { User } from "./auth";

export type AuditLog = {
  id: string;
  actor_user_id: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  metadata_json: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
};

export type OAuthClient = {
  client_id: string;
  name: string;
  redirect_uris: string[];
  is_confidential: boolean;
};

export type ListResponse<T> = {
  items: T[];
  total: number;
};

export function listUsers(limit = 50, offset = 0) {
  return api<ListResponse<User>>(
    `/admin/users?limit=${limit}&offset=${offset}`,
  );
}

export function updateUser(
  userId: string,
  body: { is_active?: boolean; is_admin?: boolean },
) {
  return api<User>(`/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function listAuditLogs(limit = 50, offset = 0, action?: string) {
  const q = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (action) q.set("action", action);
  return api<ListResponse<AuditLog>>(`/admin/audit-logs?${q}`);
}

export function listOAuthClients(limit = 50, offset = 0) {
  return api<ListResponse<OAuthClient>>(
    `/admin/oauth/clients?limit=${limit}&offset=${offset}`,
  );
}

export function createOAuthClient(body: {
  name: string;
  client_id: string;
  redirect_uris: string[];
  is_confidential: boolean;
  client_secret?: string;
}) {
  return api<OAuthClient>("/admin/oauth/clients", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateOAuthClient(
  clientId: string,
  body: {
    name?: string;
    redirect_uris?: string[];
    client_secret?: string;
  },
) {
  return api<OAuthClient>(`/admin/oauth/clients/${clientId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function deleteOAuthClient(clientId: string) {
  return api<{ message: string }>(`/admin/oauth/clients/${clientId}`, {
    method: "DELETE",
  });
}
