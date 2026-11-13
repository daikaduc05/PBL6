"use client";

import { useState } from "react";
import {
  BookOpen,
  Plus,
  Pencil,
  Trash2,
  Send,
  Loader2,
  X,
  Eye,
  CheckCircle2,
  Clock,
  XCircle,
  FileEdit,
} from "lucide-react";
import {
  useAdminLessons,
  useCreateLesson,
  useUpdateLesson,
  useDeleteLesson,
  useSubmitLesson,
} from "@/hooks/use-admin-lessons";
import { useAdminCategories } from "@/hooks/use-admin-categories";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge, VipBadge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import type { Lesson, LessonLevel, LessonAccess } from "@/types/content";

const LEVEL_MAP: Record<LessonLevel, { label: string; variant: "success" | "warning" | "danger" }> =
  {
    easy: { label: "Dễ", variant: "success" },
    medium: { label: "Trung bình", variant: "warning" },
    hard: { label: "Nâng cao", variant: "danger" },
  };

function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  if (s === "published") {
    return (
      <Badge variant="success" className="gap-1">
        <CheckCircle2 className="size-3" /> Xuất bản
      </Badge>
    );
  }
  if (s === "pending") {
    return (
      <Badge variant="warning" className="gap-1">
        <Clock className="size-3" /> Chờ duyệt
      </Badge>
    );
  }
  if (s === "rejected") {
    return (
      <Badge variant="danger" className="gap-1">
        <XCircle className="size-3" /> Từ chối
      </Badge>
    );
  }
  return (
    <Badge variant="neutral" className="gap-1">
      <FileEdit className="size-3" /> Bản nháp
    </Badge>
  );
}

export default function AdminLessonsPage() {
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const { data, isLoading } = useAdminLessons({
    q: search || undefined,
    level: levelFilter !== "all" ? levelFilter : undefined,
  });
  const { data: categories = [] } = useAdminCategories();

  const createMutation = useCreateLesson();
  const updateMutation = useUpdateLesson();
  const deleteMutation = useDeleteLesson();
  const submitMutation = useSubmitLesson();
  const { success, error } = useToast();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [previewLesson, setPreviewLesson] = useState<Lesson | null>(null);
  const [editingLesson, setEditingLesson] = useState<Lesson | null>(null);

  // Form states
  const [title, setTitle] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [level, setLevel] = useState<LessonLevel>("easy");
  const [access, setAccess] = useState<LessonAccess>("public");
  const [body, setBody] = useState("");

  const lessons = data?.items || [];
  const filtered = lessons.filter((l) => {
    if (statusFilter === "all") return true;
    return l.status.toLowerCase() === statusFilter.toLowerCase();
  });

  function openCreateModal() {
    setEditingLesson(null);
    setTitle("");
    setCategoryId(categories[0]?.id || "");
    setLevel("easy");
    setAccess("public");
    setBody("");
    setIsModalOpen(true);
  }

  function openEditModal(lesson: Lesson) {
    setEditingLesson(lesson);
    setTitle(lesson.title);
    setCategoryId(lesson.category_id);
    setLevel(lesson.level);
    setAccess(lesson.access);
    setBody(lesson.body || "");
    setIsModalOpen(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      error("Tiêu đề bài học không được để trống.");
      return;
    }
    if (!categoryId) {
      error("Vui lòng chọn danh mục.");
      return;
    }

    try {
      if (editingLesson) {
        await updateMutation.mutateAsync({
          id: editingLesson.id,
          title: title.trim(),
          category_id: categoryId,
          level,
          access,
          body: body.trim(),
        });
        success("Đã cập nhật bài học thành công!");
      } else {
        await createMutation.mutateAsync({
          title: title.trim(),
          category_id: categoryId,
          level,
          access,
          body: body.trim(),
        });
        success("Đã tạo bài học mới thành công (trạng thái DRAFT)!");
      }
      setIsModalOpen(false);
    } catch {
      error("Có lỗi xảy ra khi lưu bài học.");
    }
  }

  async function handleDelete(lesson: Lesson) {
    if (!confirm(`Bạn có chắc chắn muốn xóa bài học "${lesson.title}"?`)) {
      return;
    }
    try {
      await deleteMutation.mutateAsync(lesson.id);
      success("Đã xóa bài học thành công.");
    } catch {
      error("Không thể xóa bài học này.");
    }
  }

  async function handleSendForReview(lesson: Lesson) {
    if (!confirm(`Gửi bài học "${lesson.title}" vào hàng đợi kiểm duyệt để xuất bản?`)) {
      return;
    }
    try {
      await submitMutation.mutateAsync(lesson.id);
      success("Đã gửi bài học vào hàng đợi kiểm duyệt (PENDING)!");
    } catch {
      error("Không thể gửi duyệt bài học.");
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-display-sm font-bold text-text flex items-center gap-2">
            <BookOpen className="size-6 text-primary" />
            Quản lý bài học
          </h1>
          <p className="text-body-sm text-text-muted mt-1">
            Soạn thảo, quản lý bài học nháp (DRAFT) và gửi duyệt xuất bản cho học viên.
          </p>
        </div>
        <Button variant="primary" onClick={openCreateModal}>
          <Plus className="size-4 mr-1.5" />
          Soạn bài học mới
        </Button>
      </div>

      {/* Filters Card */}
      <Card>
        <CardContent className="p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <Input
                type="text"
                placeholder="Tìm bài học..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div>
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-body-sm text-text focus:border-primary focus:outline-none"
              >
                <option value="all">Tất cả cấp độ</option>
                <option value="easy">Cơ bản (Dễ)</option>
                <option value="medium">Trung bình</option>
                <option value="hard">Nâng cao (Khó)</option>
              </select>
            </div>
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-body-sm text-text focus:border-primary focus:outline-none"
              >
                <option value="all">Tất cả trạng thái</option>
                <option value="draft">Bản nháp (DRAFT)</option>
                <option value="pending">Chờ duyệt (PENDING)</option>
                <option value="published">Đã xuất bản (PUBLISHED)</option>
                <option value="rejected">Bị từ chối (REJECTED)</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lessons Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-heading-sm">Danh sách bài học ({filtered.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 text-text-muted">
              <Loader2 className="size-8 animate-spin mb-3 text-primary" />
              <p>Đang tải danh sách bài học...</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center text-text-muted">
              <p>Không tìm thấy bài học nào phù hợp với bộ lọc.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-body-sm">
                <thead className="border-b border-border bg-surface-2/50 text-caption font-semibold text-text-muted uppercase">
                  <tr>
                    <th className="px-4 py-3">Bài học</th>
                    <th className="px-4 py-3">Cấp độ</th>
                    <th className="px-4 py-3">Quyền</th>
                    <th className="px-4 py-3">Trạng thái</th>
                    <th className="px-4 py-3 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filtered.map((lesson) => {
                    const isDraft = lesson.status.toLowerCase() === "draft";
                    const isRejected = lesson.status.toLowerCase() === "rejected";
                    const canEdit = isDraft || isRejected;

                    return (
                      <tr key={lesson.id} className="hover:bg-surface-2/30 transition-colors">
                        <td className="px-4 py-3">
                          <div className="font-medium text-text">{lesson.title}</div>
                          <div className="text-caption text-text-muted line-clamp-1 max-w-sm">
                            {lesson.body || "Chưa có nội dung"}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={LEVEL_MAP[lesson.level]?.variant || "neutral"}>
                            {LEVEL_MAP[lesson.level]?.label || lesson.level}
                          </Badge>
                        </td>
                        <td className="px-4 py-3">
                          {lesson.access === "vip" ? (
                            <VipBadge />
                          ) : (
                            <span className="text-caption text-text-muted font-medium">Public</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={lesson.status} />
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setPreviewLesson(lesson)}
                              title="Xem nội dung"
                            >
                              <Eye className="size-3.5 mr-1" />
                              Xem
                            </Button>
                            {canEdit && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openEditModal(lesson)}
                                title="Chỉnh sửa"
                              >
                                <Pencil className="size-3.5 mr-1" />
                                Sửa
                              </Button>
                            )}
                            {isDraft && (
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-primary hover:bg-primary/10"
                                onClick={() => handleSendForReview(lesson)}
                                title="Gửi duyệt xuất bản"
                              >
                                <Send className="size-3.5 mr-1" />
                                Gửi duyệt
                              </Button>
                            )}
                            {canEdit && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-danger hover:bg-danger/10 hover:text-danger"
                                onClick={() => handleDelete(lesson)}
                                title="Xóa bài học"
                              >
                                <Trash2 className="size-3.5" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create / Edit Lesson Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-border bg-background p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-heading-sm font-bold text-text">
                {editingLesson ? "Chỉnh sửa bài học" : "Soạn thảo bài học mới"}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => setIsModalOpen(false)}>
                <X className="size-5" />
              </Button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-body-sm font-medium text-text mb-1">
                  Tiêu đề bài học <span className="text-danger">*</span>
                </label>
                <Input
                  type="text"
                  placeholder="VD: Unit 1: Present Simple Tense & Daily Routines"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="block text-body-sm font-medium text-text mb-1">
                    Danh mục <span className="text-danger">*</span>
                  </label>
                  <select
                    value={categoryId}
                    onChange={(e) => setCategoryId(e.target.value)}
                    className="w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-body-sm text-text focus:border-primary focus:outline-none"
                    required
                  >
                    <option value="" disabled>
                      Chọn danh mục
                    </option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-body-sm font-medium text-text mb-1">
                    Cấp độ (Level)
                  </label>
                  <select
                    value={level}
                    onChange={(e) => setLevel(e.target.value as LessonLevel)}
                    className="w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-body-sm text-text focus:border-primary focus:outline-none"
                  >
                    <option value="easy">Cơ bản (Dễ)</option>
                    <option value="medium">Trung bình</option>
                    <option value="hard">Nâng cao (Khó)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-body-sm font-medium text-text mb-1">
                    Quyền truy cập
                  </label>
                  <select
                    value={access}
                    onChange={(e) => setAccess(e.target.value as LessonAccess)}
                    className="w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-body-sm text-text focus:border-primary focus:outline-none"
                  >
                    <option value="public">Miễn phí (Public)</option>
                    <option value="vip">Dành riêng VIP</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-body-sm font-medium text-text mb-1">
                  Nội dung bài học (Markdown / Text)
                </label>
                <textarea
                  rows={8}
                  placeholder="## 1. Ngữ pháp trọng tâm&#10;- Cấu trúc...&#10;&#10;## 2. Từ vựng theo chủ đề..."
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  className="w-full rounded-md border border-border bg-surface-1 p-3 font-mono text-body-sm text-text focus:border-primary focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-border">
                <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                  Hủy
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {(createMutation.isPending || updateMutation.isPending) && (
                    <Loader2 className="size-4 animate-spin mr-1.5" />
                  )}
                  {editingLesson ? "Cập nhật bài học" : "Lưu bản nháp (DRAFT)"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {previewLesson && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-border bg-background p-6 shadow-xl space-y-4">
            <div className="flex items-start justify-between border-b border-border pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-heading-sm font-bold text-text">{previewLesson.title}</h3>
                  <Badge variant={LEVEL_MAP[previewLesson.level]?.variant || "neutral"}>
                    {LEVEL_MAP[previewLesson.level]?.label}
                  </Badge>
                  {previewLesson.access === "vip" && <VipBadge />}
                </div>
                <div className="mt-1 flex items-center gap-2 text-caption text-text-muted">
                  <span>Trạng thái:</span>
                  <StatusBadge status={previewLesson.status} />
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setPreviewLesson(null)}>
                <X className="size-5" />
              </Button>
            </div>

            <div className="rounded-lg border border-border bg-surface-1 p-4 font-mono text-body-sm text-text whitespace-pre-wrap">
              {previewLesson.body || "Bài học chưa có nội dung text/markdown."}
            </div>

            <div className="flex justify-end border-t border-border pt-3">
              <Button variant="outline" onClick={() => setPreviewLesson(null)}>
                Đóng
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
