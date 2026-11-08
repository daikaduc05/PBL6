"use client";

import * as React from "react";
import { Search, BookOpen, RotateCcw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { CategoryFilter } from "@/components/feature/category-filter";
import { LevelFilter } from "@/components/feature/level-filter";
import { LessonCard } from "@/components/feature/lesson-card";
import { useCategories } from "@/hooks/use-categories";
import { useLessons } from "@/hooks/use-lessons";
import type { LessonLevel } from "@/types/content";

export default function CategoriesPage() {
  const [selectedCategory, setSelectedCategory] = React.useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = React.useState<LessonLevel | "all">("all");
  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const [debouncedQuery, setDebouncedQuery] = React.useState<string>("");

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data: categories = [], isLoading: isLoadingCategories } = useCategories();

  const {
    data: lessonsData,
    isLoading: isLoadingLessons,
    isError: isLessonsError,
    refetch,
  } = useLessons({
    category_id: selectedCategory ?? undefined,
    level: selectedLevel,
    q: debouncedQuery || undefined,
  });

  const lessons = lessonsData?.items ?? [];

  function handleResetFilters() {
    setSelectedCategory(null);
    setSelectedLevel("all");
    setSearchQuery("");
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 text-body-sm font-semibold text-primary">
          <BookOpen className="size-4" aria-hidden />
          <span>Kho tài liệu học tập</span>
        </div>
        <h1 className="text-h1 text-text">Khám phá bài học tiếng Anh</h1>
        <p className="text-body text-text-muted">
          Lựa chọn chủ đề bài học và cấp độ phù hợp để rèn luyện kỹ năng ngữ pháp, từ vựng và bài
          tập trắc nghiệm.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="space-y-4 rounded-xl border border-border bg-surface p-4 shadow-xs sm:p-6">
        <div className="relative">
          <Search
            className="absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-text-muted"
            aria-hidden
          />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm bài học theo tiêu đề hoặc từ khóa..."
            className="pl-10 text-body"
          />
        </div>

        {/* Categories row */}
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
            Chủ đề bài học
          </div>
          {isLoadingCategories ? (
            <div className="flex items-center gap-2 py-1 text-body-sm text-text-muted">
              <Spinner className="size-4" />
              <span>Đang tải danh mục...</span>
            </div>
          ) : (
            <CategoryFilter
              categories={categories}
              selectedCategoryId={selectedCategory}
              onSelectCategory={setSelectedCategory}
            />
          )}
        </div>

        {/* Level filter row */}
        <div className="border-t border-border/50 pt-3">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
            Cấp độ
          </div>
          <LevelFilter value={selectedLevel} onChange={setSelectedLevel} />
        </div>
      </div>

      {/* Lessons List Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-h3 text-text">
            Danh sách bài học
            {!isLoadingLessons && (
              <span className="ml-2 text-body-sm font-normal text-text-muted">
                ({lessons.length} bài)
              </span>
            )}
          </h2>

          {(selectedCategory !== null || selectedLevel !== "all" || searchQuery !== "") && (
            <Button variant="ghost" size="sm" onClick={handleResetFilters}>
              <RotateCcw className="size-3.5" aria-hidden />
              Đặt lại bộ lọc
            </Button>
          )}
        </div>

        {isLoadingLessons ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((idx) => (
              <div
                key={idx}
                className="h-64 animate-pulse rounded-lg border border-border bg-surface-2/60"
              />
            ))}
          </div>
        ) : isLessonsError ? (
          <div className="rounded-xl border border-danger/20 bg-danger/5 p-8 text-center space-y-3">
            <p className="text-body text-danger">
              Không thể tải danh sách bài học. Vui lòng thử lại sau.
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Thử lại
            </Button>
          </div>
        ) : lessons.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border bg-surface/50 p-12 text-center space-y-4">
            <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-surface-2 text-text-muted">
              <BookOpen className="size-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-h3 text-text">Chưa tìm thấy bài học phù hợp</h3>
              <p className="text-body-sm text-text-muted">
                Hãy thử thay đổi từ khóa tìm kiếm hoặc chọn chủ đề và cấp độ khác.
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={handleResetFilters}>
              Xem tất cả bài học
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {lessons.map((lesson) => (
              <LessonCard key={lesson.id} lesson={lesson} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
