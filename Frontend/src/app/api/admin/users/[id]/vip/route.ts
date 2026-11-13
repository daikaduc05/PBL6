import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { accountApi, backendErrorResponse } from "@/lib/backend-client";
import type { UserProfile } from "@/types/api";

export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
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
      {
        error: {
          code: "FORBIDDEN",
          message: "Chỉ Admin mới có quyền cập nhật quyền VIP thủ công.",
        },
      },
      { status: 403 },
    );
  }

  const { id } = await params;
  try {
    const body = await req.json();
    const data = await accountApi.patch<UserProfile>(`/admin/users/${id}/vip`, body, { user });
    return NextResponse.json(data);
  } catch (err) {
    return backendErrorResponse(err);
  }
}
