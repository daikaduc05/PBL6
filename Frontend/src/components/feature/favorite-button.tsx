"use client";

import { Bookmark } from "lucide-react";
import { useFavoriteStatus, useToggleFavorite } from "@/hooks/use-favorites";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

export function FavoriteButton({ lessonId, className }: { lessonId: string; className?: string }) {
  const { data } = useFavoriteStatus(lessonId);
  const toggleMutation = useToggleFavorite(lessonId);
  const { success, error } = useToast();

  const isFavorite = data?.is_favorite ?? false;

  async function handleToggle(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    try {
      const willBeFavorite = !isFavorite;
      await toggleMutation.mutateAsync(isFavorite);
      if (willBeFavorite) {
        success("Đã thêm bài học vào mục yêu thích!");
      } else {
        success("Đã xóa bài học khỏi mục yêu thích.");
      }
    } catch {
      error("Có lỗi xảy ra khi cập nhật yêu thích.");
    }
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn("h-8 w-8 p-0 rounded-full hover:bg-surface-2", className)}
      onClick={handleToggle}
      disabled={toggleMutation.isPending}
      aria-label={isFavorite ? "Bỏ yêu thích" : "Yêu thích bài học"}
      title={isFavorite ? "Bỏ yêu thích" : "Lưu vào mục yêu thích"}
    >
      <Bookmark
        className={cn(
          "size-4 transition-colors",
          isFavorite ? "fill-primary text-primary" : "text-text-muted hover:text-primary",
        )}
      />
    </Button>
  );
}
