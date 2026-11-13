import { NextRequest } from "next/server";
import { notificationApi, proxyToBackend } from "@/lib/backend-client";

// GET /api/notifications?page=1&size=20&unread_only=false&type=STUDY_REMINDER
//
// Query string is forwarded as-is rather than parsed: the backend already
// validates every one of these (page>=1, size<=100, type an enum) and answers
// 422 in the shared error envelope. Re-checking here would mean two
// validators to keep in step, with this one silently winning.
export async function GET(req: NextRequest) {
  const query = req.nextUrl.search;
  return proxyToBackend((user) => notificationApi.get(`/notifications${query}`, { user }));
}
