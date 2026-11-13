"use client";

import { useState } from "react";
import Link from "next/link";
import { Bookmark, BookOpen, Loader2 } from "lucide-react";
import { useFavorites } from "@/hooks/use-favorites";
import { LessonCard } from "@/components/feature/lesson-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function FavoritesPage() {
  const { data, isLoading } = useFavorites();
  const [search, setSearch] = useState("");

  const items = data?.items || [];
  const filtered = items.filter((lesson) =>
    lesson.title.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-display-sm font-bold text-text flex items-center gap-2">
            <Bookmark className="size-6 text-primary fill-primary" />
            Bài học yêu thích
          </h1>
          <p className="text-body-sm text-text-muted mt-1">
            Danh sách bài học bạn đã lưu để tiện xem lại và ôn tập.
          </p>
        </div>
        {items.length > 0 && (
          <div className="w-full sm:w-64">
            <Input
              type="text"
              placeholder="Tìm trong mục đã lưu..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        )}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16 text-text-muted">
          <Loader2 className="size-8 animate-spin mb-3 text-primary" />
          <p className="text-body-sm">Đang tải danh sách bài học yêu thích...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed border-border rounded-xl bg-surface-1/50 p-8">
          <div className="size-14 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-4">
            <Bookmark className="size-7" />
          </div>
          <h3 className="text-heading-sm font-bold text-text">Chưa có bài học yêu thích nào</h3>
          <p className="text-body-sm text-text-muted mt-1 max-w-md">
            Khi duyệt danh sách bài học, hãy bấm vào biểu tượng Bookmark để lưu bài học vào đây và
            xem lại bất cứ lúc nào.
          </p>
          <div className="mt-6">
            <Link href="/categories">
              <Button variant="primary">
                <BookOpen className="size-4 mr-2" />
                Khám phá bài học ngay
              </Button>
            </Link>
          </div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-12 text-center text-text-muted">
          <p className="text-body-sm">
            Không tìm thấy bài học nào phù hợp với từ khóa &quot;{search}&quot;.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((lesson) => (
            <LessonCard key={lesson.id} lesson={lesson} />
          ))}
        </div>
      )}
    </div>
  );
}
