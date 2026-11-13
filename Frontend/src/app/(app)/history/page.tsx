"use client";

import * as React from "react";
import Link from "next/link";
import {
  History,
  Calendar,
  BookOpen,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useHistory } from "@/hooks/use-history";
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

export default function HistoryPage() {
  const { data: attempts = [], isLoading, isError, refetch } = useHistory();
  const [searchTerm, setSearchTerm] = React.useState("");

  const filtered = React.useMemo(() => {
    if (!searchTerm.trim()) return attempts;
    const term = searchTerm.toLowerCase();
    return attempts.filter(
      (a) =>
        (a.lesson_title || "").toLowerCase().includes(term) ||
        (a.level || "").toLowerCase().includes(term),
    );
  }, [attempts, searchTerm]);

  // Calculate statistics
  const totalCompleted = attempts.length;
  const avgScore = totalCompleted
    ? Math.round(attempts.reduce((sum, a) => sum + a.highest_score, 0) / totalCompleted)
    : 0;
  const passedCount = attempts.filter((a) => a.highest_score >= 80).length;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 text-body-sm font-semibold text-primary">
          <History className="size-4" aria-hidden />
          <span>Theo dõi tiến độ</span>
        </div>
        <h1 className="text-h1 text-text">Lịch sử làm bài & Điểm số</h1>
        <p className="text-body text-text-muted">
          Xem lại kết quả các bài kiểm tra đã hoàn thành và ôn luyện lại những phần kiến thức chưa
          vững.
        </p>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="border-border">
          <CardHeader className="p-5 pb-2">
            <CardTitle className="text-body-sm font-medium text-text-muted">
              Bài học đã hoàn thành
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-0">
            <div className="text-h1 font-bold text-text">{totalCompleted}</div>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="p-5 pb-2">
            <CardTitle className="text-body-sm font-medium text-text-muted">
              Điểm trung bình
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-0">
            <div className="text-h1 font-bold text-primary">{avgScore} / 100</div>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="p-5 pb-2">
            <CardTitle className="text-body-sm font-medium text-text-muted">
              Bài đạt chuẩn (≥ 80 điểm)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-0">
            <div className="text-h1 font-bold text-success">{passedCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search
            className="absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-text-muted"
            aria-hidden
          />
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Tìm kiếm bài học trong lịch sử..."
            className="pl-10 text-body"
          />
        </div>
      </div>

      {/* History List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-20 animate-pulse rounded-xl border border-border bg-surface-2/60"
              />
            ))}
          </div>
        ) : isError ? (
          <div className="rounded-xl border border-danger/20 bg-danger/5 p-8 text-center space-y-3">
            <p className="text-body text-danger">
              Không thể tải lịch sử làm bài. Vui lòng thử lại sau.
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Thử lại
            </Button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border bg-surface/50 p-12 text-center space-y-4">
            <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-surface-2 text-text-muted">
              <History className="size-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-h3 text-text">
                {searchTerm
                  ? "Không tìm thấy bài học nào phù hợp"
                  : "Bạn chưa hoàn thành bài kiểm tra nào"}
              </h3>
              <p className="text-body-sm text-text-muted">
                {searchTerm
                  ? "Hãy thử tìm kiếm với từ khóa khác."
                  : "Khám phá danh sách bài học và làm bài trắc nghiệm để ghi nhận điểm số tại đây."}
              </p>
            </div>
            {!searchTerm && (
              <Button asChild size="sm">
                <Link href="/categories">
                  <BookOpen className="size-4" />
                  Khám phá bài học ngay
                </Link>
              </Button>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((item) => {
              const level = item.level || "easy";
              const levelInfo = LEVEL_LABELS[level];
              const isPassed = item.highest_score >= 80;

              return (
                <div
                  key={item.id}
                  className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-5 shadow-xs transition-colors hover:border-primary/30 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="space-y-1.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={levelInfo.variant}>{levelInfo.label}</Badge>
                      <span className="flex items-center gap-1 text-xs text-text-muted">
                        <Calendar className="size-3.5" aria-hidden />
                        {formatDate(item.completed_at)}
                      </span>
                    </div>
                    <h3 className="text-h3 text-text font-semibold">
                      {item.lesson_title || `Bài học #${item.lesson_id.slice(0, 8)}`}
                    </h3>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 sm:gap-6">
                    {/* Score badge */}
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <div className="text-xs text-text-muted">Điểm cao nhất</div>
                        <div
                          className={`text-h2 font-bold ${
                            isPassed
                              ? "text-success"
                              : item.highest_score >= 50
                                ? "text-warning"
                                : "text-danger"
                          }`}
                        >
                          {item.highest_score}{" "}
                          <span className="text-xs font-normal text-text-muted">/ 100</span>
                        </div>
                      </div>
                      <div className="flex size-9 items-center justify-center rounded-full bg-surface-2">
                        {isPassed ? (
                          <CheckCircle2 className="size-5 text-success" />
                        ) : (
                          <AlertCircle className="size-5 text-warning" />
                        )}
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center gap-2">
                      <Button asChild variant="outline" size="sm">
                        <Link href={`/lessons/${item.lesson_id}`}>
                          <BookOpen className="size-4" />
                          Xem bài
                        </Link>
                      </Button>
                      <Button asChild size="sm">
                        <Link href={`/quiz/${item.lesson_id}`}>
                          <RotateCcw className="size-4" />
                          Làm lại
                        </Link>
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
