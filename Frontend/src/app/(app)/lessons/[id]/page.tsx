"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ChevronLeft,
  Calendar,
  Award,
  BookOpen,
  ArrowRight,
  Headphones,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge, VipBadge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { AudioPlayer } from "@/components/feature/audio-player";
import { VipGate } from "@/components/feature/vip-gate";
import { useLesson, useLessonMedia } from "@/hooks/use-lesson";
import { useProfile } from "@/hooks/use-profile";
import { formatDate } from "@/lib/utils";
import type { LessonLevel } from "@/types/content";

const LEVEL_LABELS: Record<
  LessonLevel,
  { label: string; variant: "success" | "warning" | "danger" }
> = {
  easy: { label: "Cơ bản", variant: "success" },
  medium: { label: "Trung bình", variant: "warning" },
  hard: { label: "Nâng cao", variant: "danger" },
};

export default function LessonDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const lessonId = params.id;

  const { data: lesson, isLoading, isError } = useLesson(lessonId);
  const { data: mediaList = [] } = useLessonMedia(lessonId);
  const { data: profile } = useProfile();

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3">
        <Spinner className="size-8" />
        <p className="text-body-sm text-text-muted">Đang tải nội dung bài học...</p>
      </div>
    );
  }

  if (isError || !lesson) {
    return (
      <div className="mx-auto max-w-xl py-12 text-center space-y-4">
        <div className="rounded-xl border border-danger/20 bg-danger/5 p-8 space-y-3">
          <p className="text-body text-danger">
            Không tìm thấy bài học hoặc bài học chưa được xuất bản.
          </p>
          <Button variant="outline" size="sm" onClick={() => router.push("/categories")}>
            <ChevronLeft className="size-4" />
            Quay lại danh mục
          </Button>
        </div>
      </div>
    );
  }

  const levelInfo = LEVEL_LABELS[lesson.level] ?? {
    label: lesson.level,
    variant: "neutral" as const,
  };
  const isLessonVip = lesson.access === "vip";
  const isUserVip = Boolean(profile?.is_vip);
  const audioMedia = mediaList.find((m) => m.kind === "audio");
  const imageMedia = mediaList.filter((m) => m.kind === "image");

  return (
    <article className="mx-auto max-w-3xl space-y-8">
      {/* Navigation Breadcrumb */}
      <div>
        <Link
          href="/categories"
          className="inline-flex items-center gap-1.5 text-body-sm font-medium text-text-muted hover:text-text transition-colors"
        >
          <ChevronLeft className="size-4" aria-hidden />
          <span>Tất cả bài học</span>
        </Link>
      </div>

      {/* Header section */}
      <header className="space-y-4 border-b border-border pb-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={levelInfo.variant}>{levelInfo.label}</Badge>
          {isLessonVip && <VipBadge />}
          <span className="flex items-center gap-1 text-xs text-text-muted">
            <Calendar className="size-3.5" aria-hidden />
            {formatDate(lesson.created_at)}
          </span>
        </div>

        <h1 className="text-h1 text-text leading-tight">{lesson.title}</h1>
      </header>

      {/* If this is a VIP lesson and user is not VIP, show VipGate */}
      {isLessonVip && !isUserVip ? (
        <VipGate isVip={isUserVip}>
          {/* Will render paywall card */}
          <div />
        </VipGate>
      ) : (
        <>
          {/* Audio Player Section if audio exists */}
          {audioMedia && (
            <section aria-labelledby="audio-section-title" className="space-y-2">
              <h2 id="audio-section-title" className="text-h3 flex items-center gap-2 text-text">
                <Headphones className="size-5 text-primary" aria-hidden />
                <span>Phần luyện nghe</span>
              </h2>
              <AudioPlayer src={audioMedia.cdn_url} title={`Audio: ${lesson.title}`} />
            </section>
          )}

          {/* Images preview if any */}
          {imageMedia.length > 0 && (
            <section className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {imageMedia.map((img) => (
                <div
                  key={img.id}
                  className="overflow-hidden rounded-xl border border-border bg-surface-2"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={img.cdn_url}
                    alt={lesson.title}
                    loading="lazy"
                    className="h-48 w-full object-cover"
                  />
                </div>
              ))}
            </section>
          )}

          {/* Lesson Body Content */}
          <section className="prose prose-neutral max-w-none space-y-4 text-body text-text leading-relaxed">
            {lesson.body ? (
              lesson.body.split("\n\n").map((para, i) => {
                const trimmed = para.trim();
                if (trimmed.startsWith("###")) {
                  return (
                    <h3 key={i} className="pt-2 text-h3 text-text font-semibold">
                      {trimmed.replace(/^###\s*/, "")}
                    </h3>
                  );
                }
                if (trimmed.startsWith("##")) {
                  return (
                    <h2 key={i} className="pt-4 text-h2 text-text font-bold">
                      {trimmed.replace(/^##\s*/, "")}
                    </h2>
                  );
                }
                if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
                  const items = trimmed.split("\n");
                  return (
                    <ul key={i} className="space-y-1.5 pl-5 list-disc text-text">
                      {items.map((it, idx) => (
                        <li key={idx}>{it.replace(/^[-*]\s*/, "")}</li>
                      ))}
                    </ul>
                  );
                }
                return (
                  <p key={i} className="text-body text-text">
                    {trimmed}
                  </p>
                );
              })
            ) : (
              <div className="rounded-lg border border-border bg-surface-2/40 p-6 text-center text-text-muted">
                Nội dung chi tiết bài học đang được biên soạn.
              </div>
            )}
          </section>

          {/* Quiz Call to action box */}
          <section className="rounded-xl border border-primary/20 bg-primary/5 p-6 sm:p-8 space-y-4 shadow-xs">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-h3 font-semibold text-text">
                  <Award className="size-5 text-primary" aria-hidden />
                  <span>Kiểm tra kiến thức bài học</span>
                </div>
                <p className="text-body-sm text-text-muted">
                  Làm bài quiz trắc nghiệm để củng cố kiến thức và ghi nhận điểm số vào lộ trình học
                  tập của bạn.
                </p>
              </div>

              <Button asChild size="lg" className="shrink-0">
                <Link href={`/quiz/${lesson.id}`}>
                  <BookOpen className="size-4" aria-hidden />
                  Bắt đầu Quiz
                  <ArrowRight className="size-4 ml-1" aria-hidden />
                </Link>
              </Button>
            </div>

            <div className="grid grid-cols-1 gap-2 pt-2 sm:grid-cols-3 border-t border-primary/10 text-xs text-text-muted">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="size-3.5 text-success" />
                <span>Câu hỏi trắc nghiệm chuẩn</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="size-3.5 text-success" />
                <span>Chấm điểm và giải thích tức thì</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="size-3.5 text-success" />
                <span>Lưu lịch sử ôn tập</span>
              </div>
            </div>
          </section>
        </>
      )}
    </article>
  );
}
