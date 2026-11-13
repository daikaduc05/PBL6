"use client";

import { useState } from "react";
import { Check, Eye, FileText, Loader2, RefreshCw, ShieldAlert, X } from "lucide-react";
import { usePendingLessons, useApproveLesson, useRejectLesson } from "@/hooks/use-moderation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge, VipBadge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import type { Lesson } from "@/types/content";

const LEVEL_CONFIG: Record<string, { label: string; variant: "success" | "warning" | "danger" }> = {
  easy: { label: "Dễ", variant: "success" },
  medium: { label: "Trung bình", variant: "warning" },
  hard: { label: "Khó", variant: "danger" },
};

export default function ModerationPage() {
  const { data, isLoading, refetch, isRefetching } = usePendingLessons();
  const approveMutation = useApproveLesson();
  const rejectMutation = useRejectLesson();
  const { success, error } = useToast();

  const [previewLesson, setPreviewLesson] = useState<Lesson | null>(null);
  const [rejectingLesson, setRejectingLesson] = useState<Lesson | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const pendingLessons = data?.items || [];

  async function handleApprove(lesson: Lesson) {
    if (!confirm(`Bạn có chắc chắn muốn duyệt và xuất bản bài học "${lesson.title}"?`)) {
      return;
    }
    try {
      await approveMutation.mutateAsync(lesson.id);
      success("Đã duyệt và xuất bản bài học thành công!");
      if (previewLesson?.id === lesson.id) setPreviewLesson(null);
    } catch {
      error("Có lỗi xảy ra khi duyệt bài học.");
    }
  }

  async function handleConfirmReject() {
    if (!rejectingLesson) return;
    try {
      await rejectMutation.mutateAsync({
        lessonId: rejectingLesson.id,
        reason: rejectReason.trim() || undefined,
      });
      success("Đã từ chối bài học.");
      setRejectingLesson(null);
      setRejectReason("");
      if (previewLesson?.id === rejectingLesson.id) setPreviewLesson(null);
    } catch {
      error("Có lỗi xảy ra khi từ chối bài học.");
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-display-sm font-bold text-text flex items-center gap-2">
            <ShieldAlert className="size-6 text-primary" />
            Hàng đợi kiểm duyệt bài học
          </h1>
          <p className="text-body-sm text-text-muted mt-1">
            Xem xét và phê duyệt các bài học đang chờ xuất bản từ đội ngũ biên tập.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isLoading || isRefetching}
          className="self-start sm:self-auto"
        >
          <RefreshCw className={`size-4 mr-2 ${isRefetching ? "animate-spin" : ""}`} />
          Làm mới
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-body-sm font-medium text-text-muted">
              Đang chờ duyệt
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-display-sm font-bold text-primary">{pendingLessons.length}</div>
            <p className="text-caption text-text-muted mt-1">Bài học cần xử lý</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-body-sm font-medium text-text-muted">
              Bài học Miễn phí
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-display-sm font-bold text-success">
              {pendingLessons.filter((l) => l.access === "public").length}
            </div>
            <p className="text-caption text-text-muted mt-1">Phục vụ mọi học viên</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-body-sm font-medium text-text-muted">Bài học VIP</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-display-sm font-bold text-warning">
              {pendingLessons.filter((l) => l.access === "vip").length}
            </div>
            <p className="text-caption text-text-muted mt-1">Dành riêng thành viên VIP</p>
          </CardContent>
        </Card>
      </div>

      {/* Table Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-heading-sm">Danh sách bài học chờ duyệt</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 text-text-muted">
              <Loader2 className="size-8 animate-spin mb-3 text-primary" />
              <p>Đang tải danh sách bài học...</p>
            </div>
          ) : pendingLessons.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="size-12 rounded-full bg-success/10 text-success flex items-center justify-center mb-3">
                <Check className="size-6" />
              </div>
              <h3 className="text-heading-sm font-semibold text-text">
                Hàng đợi kiểm duyệt trống!
              </h3>
              <p className="text-body-sm text-text-muted mt-1 max-w-sm">
                Tất cả bài học gửi lên đã được duyệt hoặc xử lý xong.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-body-sm">
                <thead className="border-b border-border bg-surface-2/50 text-caption font-semibold text-text-muted uppercase">
                  <tr>
                    <th className="px-4 py-3">Bài học</th>
                    <th className="px-4 py-3">Cấp độ</th>
                    <th className="px-4 py-3">Quyền truy cập</th>
                    <th className="px-4 py-3">Ngày gửi</th>
                    <th className="px-4 py-3 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {pendingLessons.map((lesson) => (
                    <tr key={lesson.id} className="hover:bg-surface-2/30 transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-medium text-text">{lesson.title}</div>
                        <div className="text-caption text-text-muted">
                          ID: {lesson.id.slice(0, 8)}...
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={LEVEL_CONFIG[lesson.level.toLowerCase()]?.variant || "neutral"}
                        >
                          {LEVEL_CONFIG[lesson.level.toLowerCase()]?.label || lesson.level}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        {lesson.access === "vip" ? (
                          <VipBadge />
                        ) : (
                          <span className="inline-flex items-center rounded px-2 py-0.5 text-caption font-medium bg-surface-2 text-text-muted">
                            Public
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-text-muted">
                        {new Date(lesson.created_at).toLocaleDateString("vi-VN", {
                          hour: "2-digit",
                          minute: "2-digit",
                          day: "2-digit",
                          month: "2-digit",
                          year: "numeric",
                        })}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPreviewLesson(lesson)}
                          >
                            <Eye className="size-3.5 mr-1" />
                            Xem
                          </Button>
                          <Button
                            variant="primary"
                            size="sm"
                            className="bg-success hover:bg-success/90 text-white"
                            onClick={() => handleApprove(lesson)}
                            disabled={approveMutation.isPending}
                          >
                            <Check className="size-3.5 mr-1" />
                            Duyệt
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => setRejectingLesson(lesson)}
                            disabled={rejectMutation.isPending}
                          >
                            <X className="size-3.5 mr-1" />
                            Từ chối
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Preview Modal */}
      {previewLesson && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-border bg-background p-6 shadow-xl">
            <div className="flex items-start justify-between border-b border-border pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-heading-sm font-bold text-text">{previewLesson.title}</h2>
                  <Badge
                    variant={LEVEL_CONFIG[previewLesson.level.toLowerCase()]?.variant || "neutral"}
                  >
                    {LEVEL_CONFIG[previewLesson.level.toLowerCase()]?.label || previewLesson.level}
                  </Badge>
                  {previewLesson.access === "vip" && <VipBadge />}
                </div>
                <p className="text-caption text-text-muted mt-1">ID: {previewLesson.id}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setPreviewLesson(null)}>
                <X className="size-5" />
              </Button>
            </div>

            <div className="py-4 space-y-4">
              <div>
                <h4 className="text-body-sm font-semibold text-text mb-2 flex items-center gap-1.5">
                  <FileText className="size-4 text-primary" />
                  Nội dung bài học
                </h4>
                <div className="rounded-lg border border-border bg-surface-1 p-4 font-mono text-body-sm text-text whitespace-pre-wrap">
                  {previewLesson.body || "Bài học chưa có nội dung text/markdown."}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 border-t border-border pt-4">
              <Button
                variant="destructive"
                onClick={() => {
                  setRejectingLesson(previewLesson);
                  setPreviewLesson(null);
                }}
              >
                <X className="size-4 mr-1.5" />
                Từ chối
              </Button>
              <Button
                variant="primary"
                className="bg-success hover:bg-success/90 text-white"
                onClick={() => handleApprove(previewLesson)}
              >
                <Check className="size-4 mr-1.5" />
                Duyệt xuất bản
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Modal with Reason */}
      {rejectingLesson && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-border bg-background p-6 shadow-xl space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-heading-sm font-bold text-text">Từ chối duyệt bài học</h3>
                <p className="text-body-sm text-text-muted mt-1">
                  Bài học: <span className="font-semibold">{rejectingLesson.title}</span>
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setRejectingLesson(null)}>
                <X className="size-4" />
              </Button>
            </div>

            <div>
              <label htmlFor="reason" className="block text-body-sm font-medium text-text mb-1.5">
                Lý do từ chối (gửi tới tác giả)
              </label>
              <textarea
                id="reason"
                rows={3}
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="VD: Cần bổ sung ví dụ minh họa và kiểm tra lại câu số 3..."
                className="w-full rounded-md border border-border bg-surface-1 p-2.5 text-body-sm text-text focus:border-primary focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setRejectingLesson(null)}>
                Hủy
              </Button>
              <Button
                variant="destructive"
                onClick={handleConfirmReject}
                disabled={rejectMutation.isPending}
              >
                {rejectMutation.isPending && <Loader2 className="size-4 animate-spin mr-1.5" />}
                Xác nhận từ chối
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
