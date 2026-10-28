"use client";

import type { ApiError } from "@/types/api";

export class ClientApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

async function throwFor(res: Response): Promise<never> {
  let parsed: ApiError | null = null;
  try {
    parsed = (await res.json()) as ApiError;
  } catch {
    // non-JSON error body — fall through to the generic message below
  }
  throw new ClientApiError(
    res.status,
    parsed?.error.code ?? "UNKNOWN",
    parsed?.error.message ?? res.statusText,
  );
}

/** Calls this app's own /api/* route handlers (same-origin, cookies sent
 * automatically) — never the backend services directly (frontend.md §6:
 * "No inline fetch in a component — go through api-client"). On a 401,
 * tries /api/auth/refresh once and retries the original request
 * (frontend.md §5 point 4); a second failure propagates so the caller can
 * redirect to /login. */
async function request<T>(path: string, init: RequestInit = {}, isRetry = false): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init.headers },
  });

  if (res.status === 401 && !isRetry && path !== "/api/auth/refresh") {
    const refreshed = await fetch("/api/auth/refresh", { method: "POST" });
    if (refreshed.ok) {
      return request<T>(path, init, true);
    }
  }

  if (!res.ok) return throwFor(res);

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "PATCH",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
};
