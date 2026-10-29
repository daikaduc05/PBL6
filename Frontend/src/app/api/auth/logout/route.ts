import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { accountApi } from "@/lib/backend-client";
import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/session";

export async function POST() {
  const store = await cookies();
  const refreshToken = store.get(REFRESH_COOKIE)?.value;

  // Best-effort: revoke server-side if we still have a refresh token, but
  // clear the browser's cookies regardless — the user must be able to log
  // out locally even if the backend is unreachable.
  if (refreshToken) {
    try {
      await accountApi.post("/auth/logout", { refresh_token: refreshToken });
    } catch {
      // ignored — see comment above
    }
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.delete(ACCESS_COOKIE);
  res.cookies.delete(REFRESH_COOKIE);
  return res;
}
