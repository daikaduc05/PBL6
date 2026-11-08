import { NextRequest, NextResponse } from "next/server";
import { backendErrorResponse, learningApi, requireSession } from "@/lib/backend-client";
import type { QuizSubmitRequest, QuizSubmitResponse } from "@/types/quiz";

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { user, unauthorized } = await requireSession();
  if (unauthorized) return unauthorized;
  const { id } = await params;
  const body = (await req.json()) as QuizSubmitRequest;

  try {
    const result = await learningApi.post<QuizSubmitResponse>(`/quizzes/${id}/submit`, body, {
      user,
    });
    return NextResponse.json(result);
  } catch (err) {
    return backendErrorResponse(err);
  }
}
