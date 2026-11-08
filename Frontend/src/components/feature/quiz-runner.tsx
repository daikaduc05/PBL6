"use client";

import * as React from "react";
import { ChevronLeft, ChevronRight, Clock, Send, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { QuizStudentResponse, AnswerSubmit } from "@/types/quiz";

export interface QuizRunnerProps {
  quiz: QuizStudentResponse;
  onSubmit: (answers: AnswerSubmit[], durationSeconds: number) => void;
  isSubmitting?: boolean;
}

export function QuizRunner({ quiz, onSubmit, isSubmitting = false }: QuizRunnerProps) {
  const [currentIdx, setCurrentIdx] = React.useState(0);
  const [answers, setAnswers] = React.useState<Record<string, string[]>>({});
  const [secondsElapsed, setSecondsElapsed] = React.useState(0);
  const [showConfirm, setShowConfirm] = React.useState(false);

  // Timer
  React.useEffect(() => {
    const timer = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const questions = quiz.questions;
  const currentQ = questions[currentIdx];
  const totalQ = questions.length;

  if (!currentQ) {
    return (
      <div className="rounded-xl border border-border bg-surface p-8 text-center text-text-muted">
        Không có câu hỏi nào trong bài quiz này.
      </div>
    );
  }

  const selectedOptions = answers[currentQ.id] || [];

  function handleSelectOption(optionId: string) {
    if (!currentQ) return;
    if (currentQ.type === "SINGLE_CHOICE") {
      setAnswers((prev) => ({
        ...prev,
        [currentQ.id]: [optionId],
      }));
    } else {
      // MULTI_CHOICE
      setAnswers((prev) => {
        const currentSelected = prev[currentQ.id] || [];
        const exists = currentSelected.includes(optionId);
        const updated = exists
          ? currentSelected.filter((id) => id !== optionId)
          : [...currentSelected, optionId];
        return {
          ...prev,
          [currentQ.id]: updated,
        };
      });
    }
  }

  const answeredCount = Object.keys(answers).filter(
    (qId) => (answers[qId]?.length || 0) > 0,
  ).length;

  function handleTriggerSubmit() {
    if (answeredCount < totalQ) {
      setShowConfirm(true);
    } else {
      performSubmit();
    }
  }

  function performSubmit() {
    setShowConfirm(false);
    const formattedAnswers: AnswerSubmit[] = questions.map((q) => ({
      question_id: q.id,
      selected_option_ids: answers[q.id] || [],
    }));
    onSubmit(formattedAnswers, secondsElapsed);
  }

  function formatDuration(sec: number) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  }

  return (
    <div className="space-y-6">
      {/* Header with Title and Timer */}
      <div className="flex flex-col gap-3 rounded-xl border border-border bg-surface p-4 shadow-xs sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div>
          <h2 className="text-h3 text-text">{quiz.title}</h2>
          <p className="text-body-sm text-text-muted">
            Đã trả lời: <span className="font-semibold text-primary">{answeredCount}</span>/{totalQ}{" "}
            câu
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-border bg-surface-2 px-3.5 py-1.5 text-body-sm font-medium text-text">
          <Clock className="size-4 text-primary" aria-hidden />
          <span>Thời gian: {formatDuration(secondsElapsed)}</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${((currentIdx + 1) / totalQ) * 100}%` }}
        />
      </div>

      {/* Current Question Card */}
      <Card className="border-border">
        <CardHeader className="space-y-2 border-b border-border/50 pb-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-primary">
              Câu hỏi {currentIdx + 1} / {totalQ}
            </span>
            <span className="rounded-md bg-surface-2 px-2 py-0.5 text-xs text-text-muted">
              {currentQ.type === "SINGLE_CHOICE" ? "Chọn 1 đáp án" : "Chọn nhiều đáp án"}
            </span>
          </div>
          <p className="text-h3 text-text leading-snug">{currentQ.content}</p>
        </CardHeader>

        <CardContent className="space-y-3 pt-6">
          {currentQ.options.map((opt, idx) => {
            const isSelected = selectedOptions.includes(opt.id);
            const letter = String.fromCharCode(65 + idx); // A, B, C, D...

            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => handleSelectOption(opt.id)}
                className={cn(
                  "flex w-full items-center gap-3.5 rounded-xl border p-4 text-left transition-all",
                  isSelected
                    ? "border-primary bg-primary/10 shadow-xs"
                    : "border-border bg-surface hover:border-primary/40 hover:bg-surface-2/60",
                )}
              >
                <div
                  className={cn(
                    "flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors",
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "border border-border bg-surface-2 text-text-muted",
                  )}
                >
                  {letter}
                </div>
                <span
                  className={cn(
                    "text-body leading-normal",
                    isSelected ? "font-medium text-primary" : "text-text",
                  )}
                >
                  {opt.content}
                </span>
              </button>
            );
          })}
        </CardContent>

        <CardFooter className="flex items-center justify-between border-t border-border/50 pt-4">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={currentIdx === 0}
            onClick={() => setCurrentIdx((i) => i - 1)}
          >
            <ChevronLeft className="size-4" />
            Câu trước
          </Button>

          {currentIdx < totalQ - 1 ? (
            <Button type="button" size="sm" onClick={() => setCurrentIdx((i) => i + 1)}>
              Câu tiếp theo
              <ChevronRight className="size-4 ml-1" />
            </Button>
          ) : (
            <Button
              type="button"
              variant="default"
              size="sm"
              loading={isSubmitting}
              onClick={handleTriggerSubmit}
              className="bg-success text-white hover:bg-success/90"
            >
              <Send className="size-4" />
              Nộp bài thi
            </Button>
          )}
        </CardFooter>
      </Card>

      {/* Questions Navigator Grid */}
      <div className="rounded-xl border border-border bg-surface p-4 space-y-3">
        <div className="flex items-center justify-between text-body-sm text-text-muted">
          <span>Danh sách câu hỏi</span>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            loading={isSubmitting}
            onClick={handleTriggerSubmit}
            className="text-primary hover:text-primary font-semibold"
          >
            <Send className="size-3.5" />
            Nộp bài ngay
          </Button>
        </div>

        <div className="flex flex-wrap gap-2">
          {questions.map((q, idx) => {
            const isAnswered = (answers[q.id]?.length || 0) > 0;
            const isCurrent = idx === currentIdx;

            return (
              <button
                key={q.id}
                type="button"
                onClick={() => setCurrentIdx(idx)}
                className={cn(
                  "flex size-9 items-center justify-center rounded-lg text-xs font-semibold transition-all",
                  isCurrent && "ring-2 ring-primary ring-offset-2",
                  isAnswered
                    ? "bg-primary text-primary-foreground"
                    : "border border-border bg-surface-2 text-text-muted hover:bg-surface-3 hover:text-text",
                )}
                aria-label={`Đi tới câu hỏi ${idx + 1}`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>
      </div>

      {/* Confirmation Modal if unanswered questions remain */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-xl space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-start gap-3">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-warning/10 text-warning">
                <AlertCircle className="size-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-h3 text-text">Chưa hoàn thành toàn bộ bài thi</h3>
                <p className="text-body-sm text-text-muted">
                  Bạn mới trả lời{" "}
                  <span className="font-semibold text-text">
                    {answeredCount}/{totalQ}
                  </span>{" "}
                  câu hỏi. Bạn có chắc chắn muốn nộp bài ngay bây giờ không?
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowConfirm(false)}
              >
                Tiếp tục làm bài
              </Button>
              <Button
                type="button"
                size="sm"
                variant="default"
                loading={isSubmitting}
                onClick={performSubmit}
                className="bg-success text-white hover:bg-success/90"
              >
                Xác nhận nộp bài
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
