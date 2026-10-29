import "server-only";

import type { ApiError } from "@/types/api";
import { getSession, type SessionUser } from "@/lib/session";

const ACCOUNT_BASE = process.env.ACCOUNT_SERVICE_URL ?? "http://localhost:8001/api/v1";
const PAYMENT_BASE = process.env.PAYMENT_SERVICE_URL ?? "http://localhost:8004/api/v1";

export class BackendError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

interface CallOptions {
  method?: string;
  body?: unknown;
  user?: SessionUser | null;
  /** Caller already has the raw bearer token (e.g. straight after login,
   * before a session cookie exists yet) — used instead of `user` when set. */
  accessToken?: string;
}

/** Server-only fetch wrapper for calling account/payment directly — this
 * app's route handlers stand in for the not-yet-built gateway (T08/T09),
 * so THEY are what forwards X-User-Id/X-User-Roles (backend.md §7),
 * exactly like a gateway would. Never call this from a Client Component. */
async function call<T>(base: string, path: string, opts: CallOptions = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (opts.user) {
    headers["X-User-Id"] = opts.user.userId;
    headers["X-User-Roles"] = opts.user.roles.join(",");
    headers["X-User-Tier"] = opts.user.tier;
  }
  if (opts.accessToken) {
    headers.Authorization = `Bearer ${opts.accessToken}`;
  }

  const res = await fetch(`${base}${path}`, {
    method: opts.method ?? "GET",
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    cache: "no-store",
  });

  if (!res.ok) {
    let parsed: ApiError | null = null;
    try {
      parsed = (await res.json()) as ApiError;
    } catch {
      // non-JSON error body — fall through to the generic message below
    }
    throw new BackendError(
      res.status,
      parsed?.error.code ?? "UNKNOWN",
      parsed?.error.message ?? res.statusText,
    );
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const accountApi = {
  get: <T>(path: string, opts?: CallOptions) => call<T>(ACCOUNT_BASE, path, opts),
  post: <T>(path: string, body?: unknown, opts?: CallOptions) =>
    call<T>(ACCOUNT_BASE, path, { ...opts, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, opts?: CallOptions) =>
    call<T>(ACCOUNT_BASE, path, { ...opts, method: "PATCH", body }),
};

export const paymentApi = {
  post: <T>(path: string, body?: unknown, opts?: CallOptions) =>
    call<T>(PAYMENT_BASE, path, { ...opts, method: "POST", body }),
};

const UNAUTHORIZED_BODY = {
  error: { code: "UNAUTHORIZED", message: "Not logged in", details: null, request_id: "" },
};

/** Route handlers that require a session call this first: returns the
 * verified user, or null plus a ready-to-return 401 Response in the same
 * shape the backend itself would send. */
export async function requireSession(): Promise<
  { user: SessionUser; unauthorized: null } | { user: null; unauthorized: Response }
> {
  const user = await getSession();
  if (!user) {
    return { user: null, unauthorized: Response.json(UNAUTHORIZED_BODY, { status: 401 }) };
  }
  return { user, unauthorized: null };
}

/** Route handlers call this to turn a BackendError into the same
 * {error: {...}} envelope the real backend would have sent — so the
 * browser-side api-client sees one consistent shape regardless of which
 * layer actually raised the error. */
export function backendErrorResponse(err: unknown) {
  if (err instanceof BackendError) {
    return Response.json(
      { error: { code: err.code, message: err.message, details: null, request_id: "" } },
      { status: err.status },
    );
  }
  throw err;
}
