import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { backendErrorResponse, contentApi } from "@/lib/backend-client";
import type { LessonListResponse } from "@/types/content";

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
      {
        error: {
          code: "FORBIDDEN",
          message: "Chỉ Admin và Editor mới có quyền truy cập hàng đợi kiểm duyệt.",
        },
      },
      { status: 403 },
    );
  }

  try {
    const data = await contentApi.get<LessonListResponse>("/lessons?size=100", { user });
    // Filter only pending lessons for moderation queue
    const pendingItems = (data.items || []).filter((l) => l.status.toLowerCase() === "pending");

    return NextResponse.json({
      items: pendingItems,
      total: pendingItems.length,
    });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
