import { NextRequest, NextResponse } from "next/server";
import { accountApi, backendErrorResponse, requireSession } from "@/lib/backend-client";

export async function GET() {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;
  try {
    return NextResponse.json(await accountApi.get("/users/me", { user }));
  } catch (err) {
    return backendErrorResponse(err);
  }
}

export async function PATCH(req: NextRequest) {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;
  const body = await req.json();
  try {
    return NextResponse.json(await accountApi.patch("/users/me", body, { user }));
  } catch (err) {
    return backendErrorResponse(err);
  }
}
