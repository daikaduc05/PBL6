import { NextRequest, NextResponse } from "next/server";
import { accountApi, backendErrorResponse } from "@/lib/backend-client";
import { tokenPairToCookies } from "@/lib/session";
import type { TokenPair } from "@/types/api";

export async function POST(req: NextRequest) {
  const body = await req.json();
  try {
    const tokens = await accountApi.post<TokenPair>("/auth/register", body);
    const res = NextResponse.json({ ok: true });
    for (const c of tokenPairToCookies(tokens)) res.cookies.set(c.name, c.value, c.options);
    return res;
  } catch (err) {
    return backendErrorResponse(err);
  }
}
