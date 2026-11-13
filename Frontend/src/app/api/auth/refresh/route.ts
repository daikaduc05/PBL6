import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { accountApi, backendErrorResponse } from "@/lib/backend-client";
import { ACCESS_COOKIE, REFRESH_COOKIE, tokenPairToCookies } from "@/lib/session";
import type { TokenPair } from "@/types/api";

export async function POST() {
  const store = await cookies();
  const refreshToken = store.get(REFRESH_COOKIE)?.value;
  if (!refreshToken) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "No session", details: null, request_id: "" } },
      { status: 401 },
    );
  }

  try {
    const tokens = await accountApi.post<TokenPair>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    const res = NextResponse.json({ ok: true });
    for (const c of tokenPairToCookies(tokens)) res.cookies.set(c.name, c.value, c.options);
    return res;
  } catch (err) {
    // Refresh token itself is invalid/revoked/expired — clear cookies so
    // the browser doesn't keep retrying with a dead token.
    const errRes = backendErrorResponse(err);
    const out = NextResponse.json(await errRes.json(), { status: errRes.status });
    out.cookies.delete(ACCESS_COOKIE);
    out.cookies.delete(REFRESH_COOKIE);
    return out;
  }
}
