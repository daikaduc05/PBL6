import { NextRequest } from "next/server";
import { accountApi, backendErrorResponse } from "@/lib/backend-client";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    await accountApi.post<void>("/auth/reset-password", body);
    return new Response(null, { status: 204 });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
