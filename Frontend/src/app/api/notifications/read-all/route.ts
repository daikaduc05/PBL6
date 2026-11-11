import { NextResponse } from "next/server";
import { notificationApi, backendErrorResponse, requireSession } from "@/lib/backend-client";

// POST /api/notifications/read-all
//
// POST on this side, PATCH on the backend's: the browser-facing verb says
// "run this action", while the backend's says "partially update the
// collection". Both are defensible; this layer just translates.
export async function POST() {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;

  try {
    return NextResponse.json(
      await notificationApi.patch("/notifications/read-all", undefined, { user }),
    );
  } catch (err) {
    return backendErrorResponse(err);
  }
}
