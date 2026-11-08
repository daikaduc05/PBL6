import "server-only";

import { cookies } from "next/headers";
import { jwtVerify } from "jose";
import type { TokenPair } from "@/types/api";

const COOKIE_BASE = process.env.SESSION_COOKIE_NAME ?? "pbl6_session";
export const ACCESS_COOKIE = `${COOKIE_BASE}_access`;
export const REFRESH_COOKIE = `${COOKIE_BASE}_refresh`;

// frontend.md §5: tokens are never put in localStorage — a route handler
// writes them as httpOnly/Secure/SameSite=Lax cookies after calling the
// backend. Access cookie expiry tracks the token's own `expires_in`;
// refresh gets a flat 7 days matching Backend's REFRESH_TOKEN_DAYS default
// (account.config.AccountSettings.refresh_token_days).
export function sessionCookieOptions(maxAgeSeconds: number) {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: maxAgeSeconds,
  };
}

const REFRESH_MAX_AGE_SECONDS = 7 * 24 * 60 * 60;

export function tokenPairToCookies(tokens: TokenPair) {
  return [
    {
      name: ACCESS_COOKIE,
      value: tokens.access_token,
      options: sessionCookieOptions(tokens.expires_in),
    },
    {
      name: REFRESH_COOKIE,
      value: tokens.refresh_token,
      options: sessionCookieOptions(REFRESH_MAX_AGE_SECONDS),
    },
  ];
}

export interface SessionUser {
  userId: string;
  roles: string[];
  tier: string;
}

function secretKey() {
  const secret = process.env.SESSION_JWT_SECRET;
  if (!secret) throw new Error("SESSION_JWT_SECRET is not set");
  return new TextEncoder().encode(secret);
}

/** Verifies the access-token cookie server-side. Returns null for a
 * missing, expired or tampered token — callers treat that as "not logged
 * in," same as a 401 would. This app does its own verification instead of
 * trusting a gateway because there is no gateway yet (T08/T09) — see
 * .env.example. */
export async function getSession(): Promise<SessionUser | null> {
  const store = await cookies();
  const token = store.get(ACCESS_COOKIE)?.value;
  if (!token) return null;

  try {
    const { payload } = await jwtVerify(token, secretKey());
    if (payload.type !== "access" || typeof payload.sub !== "string") return null;
    return {
      userId: payload.sub,
      roles: Array.isArray(payload.roles) ? (payload.roles as string[]) : [],
      tier: typeof payload.tier === "string" ? payload.tier : "normal",
    };
  } catch {
    return null;
  }
}
