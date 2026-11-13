import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { accountApi, backendErrorResponse } from "@/lib/backend-client";
import type { UserProfile } from "@/types/api";

export async function GET() {
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
      { error: { code: "FORBIDDEN", message: "Chỉ Admin mới có quyền quản lý Editor." } },
      { status: 403 },
    );
  }

  try {
    const data = await accountApi.get<UserProfile[]>("/admin/editors", { user });
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
  if (!roles.includes("ADMIN")) {
    return NextResponse.json(
      { error: { code: "FORBIDDEN", message: "Chỉ Admin mới có quyền tạo Editor." } },
      { status: 403 },
    );
  }

  try {
    const body = await req.json();
    const data = await accountApi.post<UserProfile>("/admin/editors", body, { user });
    return NextResponse.json(data, { status: 201 });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
