import { NextResponse } from "next/server";
import { notificationApi, backendErrorResponse, requireSession } from "@/lib/backend-client";

type Params = { params: Promise<{ id: string }> };

// PATCH /api/notifications/{id} — mark one read.
export async function PATCH(_req: Request, { params }: Params) {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;

  const { id } = await params;
  try {
    await notificationApi.patch(`/notifications/${id}/read`, undefined, { user });
    return new NextResponse(null, { status: 204 });
  } catch (err) {
    return backendErrorResponse(err);
  }
}

// DELETE /api/notifications/{id}
//
// A 404 here covers both "no such id" and "belongs to someone else" — the
// backend answers the same for both on purpose, so a caller probing ids
// learns nothing from the difference. Nothing to add at this layer.
export async function DELETE(_req: Request, { params }: Params) {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;

  const { id } = await params;
  try {
    await notificationApi.del(`/notifications/${id}`, { user });
    return new NextResponse(null, { status: 204 });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
