import { notificationApi, proxyToBackend } from "@/lib/backend-client";

type Params = { params: Promise<{ id: string }> };

// PATCH /api/notifications/{id} — mark one read.
export async function PATCH(_req: Request, { params }: Params) {
  const { id } = await params;
  return proxyToBackend((user) =>
    notificationApi.patch(`/notifications/${id}/read`, undefined, { user }),
  );
}

// DELETE /api/notifications/{id}
//
// A 404 here covers both "no such id" and "belongs to someone else" — the
// backend answers the same for both on purpose, so a caller probing ids
// learns nothing from the difference. Nothing to add at this layer.
export async function DELETE(_req: Request, { params }: Params) {
  const { id } = await params;
  return proxyToBackend((user) => notificationApi.del(`/notifications/${id}`, { user }));
}
