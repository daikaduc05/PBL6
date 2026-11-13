import { NextRequest } from "next/server";
import { notificationApi, proxyToBackend } from "@/lib/backend-client";

// GET /api/notifications/settings
//
// A learner who never opened this screen has no row in the database; the
// backend answers defaults rather than 404, so the UI has nothing special
// to handle.
export async function GET() {
  return proxyToBackend((user) => notificationApi.get("/notifications/settings", { user }));
}

// PUT /api/notifications/settings
export async function PUT(req: NextRequest) {
  const body = await req.json();
  return proxyToBackend((user) => notificationApi.put("/notifications/settings", body, { user }));
}
