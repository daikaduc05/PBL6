import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { backendErrorResponse, contentApi } from "@/lib/backend-client";
import type { CategoryTreeResponse, Category } from "@/types/content";

export async function GET() {
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

  try {
    const data = await contentApi.get<CategoryTreeResponse[]>("/categories", { user });
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
      { error: { code: "FORBIDDEN", message: "Chỉ Admin và Editor mới có quyền tạo danh mục." } },
      { status: 403 },
    );
  }

  try {
    const body = await req.json();
    const data = await contentApi.post<Category>("/categories", body, { user });
    return NextResponse.json(data, { status: 201 });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
