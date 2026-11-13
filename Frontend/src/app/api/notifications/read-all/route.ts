import { notificationApi, proxyToBackend } from "@/lib/backend-client";

// POST /api/notifications/read-all
//
// POST on this side, PATCH on the backend's: the browser-facing verb says
// "run this action", while the backend's says "partially update the
// collection". Both are defensible; this layer just translates.
export async function POST() {
  return proxyToBackend((user) =>
    notificationApi.patch("/notifications/read-all", undefined, { user }),
  );
}
