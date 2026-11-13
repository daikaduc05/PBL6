import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { backendErrorResponse, contentApi, learningApi } from "@/lib/backend-client";
import type { Lesson } from "@/types/content";

interface FavoriteBackendItem {
  lesson_id: string;
  created_at: string;
}

export async function GET() {
  const user = await getSession();
  if (!user) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "Yêu cầu đăng nhập." } },
      { status: 401 },
    );
  }

  try {
    // 1. Get favorite lesson IDs from learning service
    const favorites = await learningApi.get<FavoriteBackendItem[]>("/me/favorites", { user });

    if (!favorites || favorites.length === 0) {
      return NextResponse.json({ items: [], total: 0 });
    }

    // 2. Fetch full lesson details for each favorite item
    const enriched = await Promise.all(
      favorites.map(async (fav) => {
        try {
          const lesson = await contentApi.get<Lesson>(`/lessons/${fav.lesson_id}`, { user });
          return {
            ...lesson,
            favorited_at: fav.created_at,
          };
        } catch {
          return null;
        }
      }),
    );

    const validLessons = enriched.filter(Boolean);

    return NextResponse.json({
      items: validLessons,
      total: validLessons.length,
    });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
