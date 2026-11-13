import Link from "next/link";
import { BookOpen, ArrowRight } from "lucide-react";
import { Badge, VipBadge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import type { Lesson, LessonLevel } from "@/types/content";

const LEVEL_LABELS: Record<
  LessonLevel,
  { label: string; variant: "success" | "warning" | "danger" }
> = {
  easy: { label: "Cơ bản", variant: "success" },
  medium: { label: "Trung bình", variant: "warning" },
  hard: { label: "Nâng cao", variant: "danger" },
};

export function LessonCard({ lesson }: { lesson: Lesson }) {
  const levelInfo = LEVEL_LABELS[lesson.level] ?? {
    label: lesson.level,
    variant: "neutral" as const,
  };
  const isVip = lesson.access === "vip";

  return (
    <Card className="group flex flex-col justify-between overflow-hidden border-border transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md">
      <CardHeader className="space-y-3 p-5">
        <div className="flex items-center justify-between gap-2">
          <Badge variant={levelInfo.variant}>{levelInfo.label}</Badge>
          {isVip && <VipBadge />}
        </div>
        <h3 className="line-clamp-2 text-h3 text-text transition-colors group-hover:text-primary">
          {lesson.title}
        </h3>
      </CardHeader>

      <CardContent className="p-5 pt-0">
        <p className="line-clamp-3 text-body-sm text-text-muted">
          {lesson.body
            ? lesson.body.replace(/[#*`_]/g, "").slice(0, 160)
            : "Bài học bao gồm kiến thức trọng tâm, ví dụ thực tế và bài tập trắc nghiệm."}
        </p>
      </CardContent>

      <CardFooter className="border-t border-border/50 bg-surface-2/30 p-4">
        <Link
          href={`/lessons/${lesson.id}`}
          className="inline-flex w-full items-center justify-between text-body-sm font-medium text-primary hover:underline"
        >
          <span className="inline-flex items-center gap-1.5">
            <BookOpen className="size-4" aria-hidden />
            Vào học bài
          </span>
          <ArrowRight
            className="size-4 transition-transform group-hover:translate-x-1"
            aria-hidden
          />
        </Link>
      </CardFooter>
    </Card>
  );
}
