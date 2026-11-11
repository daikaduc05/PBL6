import { NextRequest, NextResponse } from "next/server";
import { notificationApi, backendErrorResponse, requireSession } from "@/lib/backend-client";

// GET /api/notifications?page=1&size=20&unread_only=false&type=STUDY_REMINDER
export async function GET(req: NextRequest) {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;

  // Forwarded as-is rather than parsed: the backend already validates every
  // one of these (page>=1, size<=100, type an enum) and answers 422 in the
  // shared error envelope. Re-checking here would mean two validators to
  // keep in step, with this one silently winning.
  const query = req.nextUrl.search;
  try {
    return NextResponse.json(await notificationApi.get(`/notifications${query}`, { user }));
  } catch (err) {
    return backendErrorResponse(err);
  }
}
