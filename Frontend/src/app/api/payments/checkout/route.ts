import { NextRequest, NextResponse } from "next/server";
import { paymentApi, backendErrorResponse, requireSession } from "@/lib/backend-client";

export async function POST(req: NextRequest) {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;
  const body = await req.json();
  try {
    return NextResponse.json(await paymentApi.post("/payments/checkout", body, { user }));
  } catch (err) {
    return backendErrorResponse(err);
  }
}
