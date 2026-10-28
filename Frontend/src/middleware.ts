import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";

// Mirrors frontend.md §5's rule, scoped to the (app) routes this app
// actually has (profile, checkout) — middleware runs on the Edge runtime,
// which can't import "server-only" lib/session.ts (that one's for Route
// Handlers/Server Components), so the cookie read+verify is duplicated
// here minimally.
const PROTECTED_PREFIXES = ["/profile", "/checkout"];

const COOKIE_BASE = process.env.SESSION_COOKIE_NAME ?? "pbl6_session";
const ACCESS_COOKIE = `${COOKIE_BASE}_access`;

async function isAuthenticated(req: NextRequest): Promise<boolean> {
  const token = req.cookies.get(ACCESS_COOKIE)?.value;
  if (!token) return false;
  const secret = process.env.SESSION_JWT_SECRET;
  if (!secret) return false;
  try {
    await jwtVerify(token, new TextEncoder().encode(secret));
    return true;
  } catch {
    return false;
  }
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const needsAuth = PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));
  if (!needsAuth) return NextResponse.next();

  if (await isAuthenticated(req)) return NextResponse.next();

  const loginUrl = new URL("/login", req.url);
  loginUrl.searchParams.set("next", pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/profile/:path*", "/checkout/:path*"],
};
