"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ChevronLeft, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { QuizRunner } from "@/components/feature/quiz-runner";
import { QuizResult } from "@/components/feature/quiz-result";
import { useLessonQuiz, useSubmitQuiz } from "@/hooks/use-quiz";
import { useToast } from "@/hooks/use-toast";
import type { AnswerSubmit, QuizSubmitResponse } from "@/types/quiz";

export default function QuizPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;
  const toast = useToast();

  const [result, setResult] = React.useState<QuizSubmitResponse | null>(null);

  const { data: quiz, isLoading, isError, refetch } = useLessonQuiz(id);
  const submitMutation = useSubmitQuiz(quiz?.id || id);

  async function handleSubmit(answers: AnswerSubmit[], durationSeconds: number) {
    if (!quiz) return;
    try {
      const response = await submitMutation.mutateAsync({
        answers,
        duration_seconds: durationSeconds,
      });
      setResult(response);
      toast.success("Nộp bài thi thành công!");
    } catch {
      toast.error("Không thể nộp bài thi. Vui lòng kiểm tra lại kết nối.");
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3">
        <Spinner className="size-8" />
        <p className="text-body-sm text-text-muted">Đang tải bộ câu hỏi trắc nghiệm...</p>
      </div>
    );
  }

  if (isError || !quiz || quiz.questions.length === 0) {
    return (
      <div className="mx-auto max-w-lg py-12 text-center space-y-4">
        <div className="rounded-2xl border border-border bg-surface p-8 space-y-4 shadow-sm">
          <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-surface-2 text-text-muted">
            <HelpCircle className="size-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-h3 text-text">Chưa có bài quiz cho nội dung này</h3>
            <p className="text-body-sm text-text-muted">
              Bài kiểm tra trắc nghiệm đang được cập nhật hoặc hệ thống gặp sự cố tải câu hỏi.
            </p>
          </div>
          <div className="flex justify-center gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => router.back()}>
              <ChevronLeft className="size-4" />
              Quay lại
            </Button>
            <Button size="sm" onClick={() => refetch()}>
              Thử tải lại
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Back button */}
      <div>
        <Link
          href={`/lessons/${quiz.lesson_id}`}
          className="inline-flex items-center gap-1.5 text-body-sm font-medium text-text-muted hover:text-text transition-colors"
        >
          <ChevronLeft className="size-4" aria-hidden />
          <span>Quay lại bài học</span>
        </Link>
      </div>

      {result ? (
        <QuizResult quiz={quiz} result={result} onRetry={() => setResult(null)} />
      ) : (
        <QuizRunner quiz={quiz} onSubmit={handleSubmit} isSubmitting={submitMutation.isPending} />
      )}
    </div>
  );
}
