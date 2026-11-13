import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { backendErrorResponse, contentApi } from "@/lib/backend-client";
import type { Lesson } from "@/types/content";

export async function PUT(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const user = await getSession();
  if (!user) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "Yêu cầu đăng nhập." } },
      { status: 401 },
    );
  }

  const roles = user.roles.map((r) => r.toUpperCase());
  if (!roles.includes("ADMIN") && !roles.includes("EDITOR")) {
    return NextResponse.json(
      { error: { code: "FORBIDDEN", message: "Quyền truy cập bị từ chối." } },
      { status: 403 },
    );
  }

  const { id } = await params;
  try {
    const body = await req.json();
    const data = await contentApi.put<Lesson>(`/lessons/${id}`, body, { user });
    return NextResponse.json(data);
  } catch (err) {
    return backendErrorResponse(err);
  }
}

export async function DELETE(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const user = await getSession();
  if (!user) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "Yêu cầu đăng nhập." } },
      { status: 401 },
    );
  }

  const roles = user.roles.map((r) => r.toUpperCase());
  if (!roles.includes("ADMIN") && !roles.includes("EDITOR")) {
    return NextResponse.json(
      { error: { code: "FORBIDDEN", message: "Quyền truy cập bị từ chối." } },
      { status: 403 },
    );
  }

  const { id } = await params;
  try {
    await contentApi.delete(`/lessons/${id}`, { user });
    return new NextResponse(null, { status: 204 });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
