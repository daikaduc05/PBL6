import { NextRequest, NextResponse } from "next/server";
import { notificationApi, backendErrorResponse, requireSession } from "@/lib/backend-client";

// GET /api/notifications/settings
//
// A learner who never opened this screen has no row in the database; the
// backend answers defaults rather than 404, so the UI has nothing special
// to handle.
export async function GET() {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;

  try {
    return NextResponse.json(await notificationApi.get("/notifications/settings", { user }));
  } catch (err) {
    return backendErrorResponse(err);
  }
}

// PUT /api/notifications/settings
export async function PUT(req: NextRequest) {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;

  const body = await req.json();
  try {
    return NextResponse.json(await notificationApi.put("/notifications/settings", body, { user }));
  } catch (err) {
    return backendErrorResponse(err);
  }
}
