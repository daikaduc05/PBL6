import { NextRequest, NextResponse } from "next/server";
import { accountApi, backendErrorResponse, requireSession } from "@/lib/backend-client";

export async function POST(req: NextRequest) {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;
  const body = await req.json();
  try {
    await accountApi.post("/users/me/change-password", body, { user });
    return new NextResponse(null, { status: 204 });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
