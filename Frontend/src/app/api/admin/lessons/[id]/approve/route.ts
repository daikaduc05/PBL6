import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { backendErrorResponse, contentApi } from "@/lib/backend-client";
import type { Lesson } from "@/types/content";

export async function POST(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const user = await getSession();
  if (!user) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "Yêu cầu đăng nhập." } },
      { status: 401 },
    );
  }

  const roles = user.roles.map((r) => r.toUpperCase());
  if (!roles.includes("ADMIN")) {
    return NextResponse.json(
      { error: { code: "FORBIDDEN", message: "Chỉ Admin mới có quyền duyệt xuất bản bài học." } },
      { status: 403 },
    );
  }

  const { id } = await params;
  try {
    const data = await contentApi.post<Lesson>(`/lessons/${id}/approve`, undefined, { user });
    return NextResponse.json(data);
  } catch (err) {
    return backendErrorResponse(err);
  }
}
