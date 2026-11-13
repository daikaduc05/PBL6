"use client";

import Link from "next/link";
import {
  Award,
  CheckCircle2,
  XCircle,
  RotateCcw,
  BookOpen,
  Trophy,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { QuizStudentResponse, QuizSubmitResponse } from "@/types/quiz";

export interface QuizResultProps {
  quiz: QuizStudentResponse;
  result: QuizSubmitResponse;
  onRetry: () => void;
}

export function QuizResult({ quiz, result, onRetry }: QuizResultProps) {
  const isPassed = result.passed;
  const percentage = Math.round((result.correct_answers_count / result.total_questions) * 100);

  // Map question result by question_id for quick review
  const resultMap = new Map(result.results.map((r) => [r.question_id, r]));

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Score Summary Banner */}
      <Card
        className={cn(
          "overflow-hidden border-2 p-6 sm:p-8 text-center shadow-md",
          isPassed ? "border-success/40 bg-success/5" : "border-warning/40 bg-warning/5",
        )}
      >
        <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-surface shadow-sm">
          {isPassed ? (
            <Trophy className="size-8 text-success" aria-hidden />
          ) : (
            <Award className="size-8 text-warning" aria-hidden />
          )}
        </div>

        <div className="mt-4 space-y-2">
          <Badge variant={isPassed ? "success" : "warning"} className="text-body-sm px-3 py-1">
            {isPassed ? "Đạt yêu cầu bài kiểm tra" : "Chưa đạt yêu cầu"}
          </Badge>
          <h2 className="text-h1 text-text">
            Điểm số:{" "}
            <span className={isPassed ? "text-success" : "text-warning"}>{result.score}</span> / 100
          </h2>
          <p className="text-body text-text-muted">
            Bạn đã trả lời đúng{" "}
            <span className="font-semibold text-text">
              {result.correct_answers_count}/{result.total_questions}
            </span>{" "}
            câu hỏi ({percentage}%).
          </p>
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Button variant="outline" size="sm" onClick={onRetry}>
            <RotateCcw className="size-4" />
            Làm lại bài kiểm tra
          </Button>

          <Button asChild size="sm">
            <Link href={`/lessons/${result.lesson_id}`}>
              <BookOpen className="size-4" />
              Quay lại bài học
            </Link>
          </Button>

          <Button asChild variant="secondary" size="sm">
            <Link href="/categories">
              Khám phá bài học khác
              <ArrowRight className="size-4 ml-1" />
            </Link>
          </Button>
        </div>
      </Card>

      {/* Detailed Review Section */}
      <div className="space-y-4">
        <h3 className="text-h3 text-text">Chi tiết kết quả từng câu hỏi</h3>

        <div className="space-y-4">
          {quiz.questions.map((q, idx) => {
            const qResult = resultMap.get(q.id);
            const isCorrect = qResult?.is_correct ?? false;
            const selectedSet = new Set(qResult?.selected_option_ids || []);
            const correctSet = new Set(qResult?.correct_option_ids || []);

            return (
              <Card
                key={q.id}
                className={cn(
                  "border transition-colors",
                  isCorrect ? "border-success/30 bg-success/5" : "border-danger/30 bg-danger/5",
                )}
              >
                <CardHeader className="p-4 pb-2 sm:p-6 sm:pb-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <span className="text-xs font-semibold uppercase text-text-muted">
                        Câu hỏi {idx + 1}
                      </span>
                      <p className="text-h3 text-text">{q.content}</p>
                    </div>

                    <div className="flex items-center gap-1 shrink-0">
                      {isCorrect ? (
                        <div className="inline-flex items-center gap-1 rounded-full bg-success/15 px-2.5 py-0.5 text-xs font-semibold text-success">
                          <CheckCircle2 className="size-3.5" />
                          <span>Đúng</span>
                        </div>
                      ) : (
                        <div className="inline-flex items-center gap-1 rounded-full bg-danger/15 px-2.5 py-0.5 text-xs font-semibold text-danger">
                          <XCircle className="size-3.5" />
                          <span>Sai</span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-2 p-4 pt-2 sm:p-6 sm:pt-3">
                  {q.options.map((opt, optIdx) => {
                    const isSelected = selectedSet.has(opt.id);
                    const isCorrectAnswer = correctSet.has(opt.id);
                    const letter = String.fromCharCode(65 + optIdx);

                    return (
                      <div
                        key={opt.id}
                        className={cn(
                          "flex items-center justify-between gap-3 rounded-lg border p-3 text-body-sm transition-all",
                          isCorrectAnswer
                            ? "border-success bg-success/15 font-medium text-success dark:text-emerald-400"
                            : isSelected && !isCorrect
                              ? "border-danger bg-danger/15 font-medium text-danger"
                              : "border-border/60 bg-surface/80 text-text",
                        )}
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="flex size-6 shrink-0 items-center justify-center rounded-full border border-current text-xs font-bold">
                            {letter}
                          </span>
                          <span>{opt.content}</span>
                        </div>

                        <div className="text-xs font-semibold">
                          {isCorrectAnswer && <span className="text-success">Đáp án đúng</span>}
                          {isSelected && !isCorrectAnswer && (
                            <span className="text-danger">Lựa chọn của bạn</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
