import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { accountApi, contentApi, backendErrorResponse } from "@/lib/backend-client";
import type { LessonListResponse, CategoryTreeResponse } from "@/types/content";
import type { UserProfile } from "@/types/api";

interface PaginatedUsers {
  items: UserProfile[];
  total: number;
}

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
    // 1. Fetch lessons
    const lessonsData = await contentApi
      .get<LessonListResponse>("/lessons?size=100", { user })
      .catch(() => ({ items: [], total: 0 }));

    // 2. Fetch categories
    const categoriesData = await contentApi
      .get<CategoryTreeResponse[]>("/categories", { user })
      .catch(() => []);

    // 3. Fetch students (Admin only; Editor defaults to 0 if forbidden)
    let studentsData: PaginatedUsers = { items: [], total: 0 };
    if (roles.includes("ADMIN")) {
      studentsData = await accountApi
        .get<PaginatedUsers>("/admin/users?size=100", { user })
        .catch(() => ({ items: [], total: 0 }));
    }

    const items = lessonsData.items || [];
    const published = items.filter((l) => l.status.toLowerCase() === "published").length;
    const pending = items.filter((l) => l.status.toLowerCase() === "pending").length;
    const draft = items.filter((l) => l.status.toLowerCase() === "draft").length;
    const rejected = items.filter((l) => l.status.toLowerCase() === "rejected").length;

    const studentItems = studentsData.items || [];
    const vipCount = studentItems.filter((s) => s.is_vip).length;
    const lockedCount = studentItems.filter((s) => s.status === "LOCKED").length;

    return NextResponse.json({
      lessons: {
        total: items.length,
        published,
        pending,
        draft,
        rejected,
      },
      categories: {
        total: categoriesData.length,
      },
      students: {
        total: studentsData.total || studentItems.length,
        vip: vipCount,
        locked: lockedCount,
      },
    });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
