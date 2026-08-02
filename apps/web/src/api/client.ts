/**
 * API origin (includes /api prefix).
 * Local: VITE_API_URL or http://localhost:8000/api.
 * Production / shared-host build: same-origin /api.
 */
const _viteApi = import.meta.env.VITE_API_URL;
const API_URL =
  _viteApi !== undefined && _viteApi !== ""
    ? _viteApi
    : import.meta.env.DEV
      ? "http://localhost:8000/api"
      : "/api";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const data: unknown = await res.json();
    if (
      typeof data === "object" &&
      data !== null &&
      "detail" in data &&
      typeof (data as { detail: unknown }).detail === "string"
    ) {
      return (data as { detail: string }).detail;
    }
    return JSON.stringify(data);
  } catch {
    return res.statusText || "Request failed";
  }
}

export async function api<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include", // send/receive HttpOnly sid cookie
  });

  if (!res.ok) {
    throw new ApiError(res.status, await parseError(res));
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export { API_URL };
