import { NextRequest, NextResponse } from "next/server";
import { backendErrorResponse, learningApi, requireSession } from "@/lib/backend-client";
import type { QuizStudentResponse } from "@/types/quiz";

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;
  const { id } = await params;

  try {
    const quiz = await learningApi.get<QuizStudentResponse>(`/quizzes/lesson/${id}`, {
      user,
    });
    return NextResponse.json(quiz);
  } catch (err) {
    return backendErrorResponse(err);
  }
}
