import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { accountApi, backendErrorResponse } from "@/lib/backend-client";
import type { UserProfile } from "@/types/api";

interface PaginatedUsers {
  items: UserProfile[];
  total: number;
  page: number;
  size: number;
}

export async function GET(req: Request) {
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
      { error: { code: "FORBIDDEN", message: "Chỉ Admin mới có quyền quản lý người dùng." } },
      { status: 403 },
    );
  }

  const url = new URL(req.url);
  const q = url.searchParams.get("q") ?? "";
  const statusParam = url.searchParams.get("status") ?? "";

  const queryParams = new URLSearchParams({ size: "100" });
  if (q) queryParams.set("q", q);
  if (statusParam && statusParam !== "all") queryParams.set("status", statusParam);

  try {
    const data = await accountApi.get<PaginatedUsers>(`/admin/users?${queryParams.toString()}`, {
      user,
    });
    return NextResponse.json(data);
  } catch (err) {
    return backendErrorResponse(err);
  }
}
