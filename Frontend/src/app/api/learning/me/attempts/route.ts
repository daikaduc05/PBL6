import { NextResponse } from "next/server";
import {
  backendErrorResponse,
  contentApi,
  learningApi,
  requireSession,
} from "@/lib/backend-client";
import type { HistoryItem, LessonListResponse } from "@/types/content";

export async function GET() {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;

  try {
    const attempts = await learningApi.get<HistoryItem[]>("/me/attempts", { user });

    // Try to enrich with lesson title and level from content service
    try {
      const lessonsData = await contentApi.get<LessonListResponse>("/lessons?size=100", {
        user,
      });
      const lessonMap = new Map(lessonsData.items.map((l) => [l.id, l]));

      const enriched = attempts.map((att) => {
        const lesson = lessonMap.get(att.lesson_id);
        return {
          ...att,
          lesson_title: lesson ? lesson.title : "Bài học",
          level: lesson ? lesson.level : "easy",
        };
      });
      return NextResponse.json(enriched);
    } catch {
      // Fallback without lesson enrichment if content service query fails
      return NextResponse.json(attempts);
    }
  } catch (err) {
    return backendErrorResponse(err);
  }
}
