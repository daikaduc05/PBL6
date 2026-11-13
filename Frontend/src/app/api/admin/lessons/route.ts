import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { backendErrorResponse, contentApi } from "@/lib/backend-client";
import type { Lesson, LessonListResponse } from "@/types/content";

export async function GET(req: Request) {
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

  const url = new URL(req.url);
  const q = url.searchParams.get("q") ?? "";
  const level = url.searchParams.get("level") ?? "";
  const categoryId = url.searchParams.get("category_id") ?? "";

  const queryParams = new URLSearchParams({ size: "100" });
  if (q) queryParams.set("q", q);
  if (level && level !== "all") queryParams.set("level", level);
  if (categoryId) queryParams.set("category_id", categoryId);

  try {
    const data = await contentApi.get<LessonListResponse>(`/lessons?${queryParams.toString()}`, {
      user,
    });
    return NextResponse.json(data);
  } catch (err) {
    return backendErrorResponse(err);
  }
}

export async function POST(req: Request) {
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
      { error: { code: "FORBIDDEN", message: "Chỉ Admin và Editor mới có quyền tạo bài học." } },
      { status: 403 },
    );
  }

  try {
    const body = await req.json();
    const data = await contentApi.post<Lesson>("/lessons", body, { user });
    return NextResponse.json(data, { status: 201 });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
