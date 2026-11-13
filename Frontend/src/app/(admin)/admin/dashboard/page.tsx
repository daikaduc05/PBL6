"use client";

import Link from "next/link";
import {
  LayoutDashboard,
  Users,
  Crown,
  BookOpen,
  Clock,
  ArrowRight,
  ShieldCheck,
  FolderTree,
  UserCheck,
  Loader2,
  CheckCircle2,
  FileEdit,
  XCircle,
} from "lucide-react";
import { useAdminStats } from "@/hooks/use-admin-stats";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AdminDashboardPage() {
  const { data: stats, isLoading } = useAdminStats();

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center text-text-muted">
        <Loader2 className="size-8 animate-spin mb-3 text-primary" />
        <p className="text-body-sm">Đang tổng hợp số liệu thống kê hệ thống...</p>
      </div>
    );
  }

  const lessons = stats?.lessons ?? {
    total: 0,
    published: 0,
    pending: 0,
    draft: 0,
    rejected: 0,
  };
  const students = stats?.students ?? { total: 0, vip: 0, locked: 0 };
  const categories = stats?.categories ?? { total: 0 };

  const publishedPercent = lessons.total
    ? Math.round((lessons.published / lessons.total) * 100)
    : 0;
  const pendingPercent = lessons.total ? Math.round((lessons.pending / lessons.total) * 100) : 0;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-display-sm font-bold text-text flex items-center gap-2">
          <LayoutDashboard className="size-6 text-primary" />
          Bảng điều khiển quản trị
        </h1>
        <p className="text-body-sm text-text-muted mt-1">
          Tổng quan số liệu thống kê thời gian thực về học viên, bài học và kiểm duyệt.
        </p>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-body-sm font-medium text-text-muted">
              Tổng số học viên
            </CardTitle>
            <Users className="size-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-display-sm font-bold text-text">{students.total}</div>
            <p className="text-caption text-text-muted mt-1">
              {students.locked > 0
                ? `${students.locked} tài khoản bị khóa`
                : "Tất cả đang hoạt động"}
            </p>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-body-sm font-medium text-text-muted">Học viên VIP</CardTitle>
            <Crown className="size-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-display-sm font-bold text-warning">{students.vip}</div>
            <p className="text-caption text-text-muted mt-1">
              {students.total
                ? `${Math.round((students.vip / students.total) * 100)}% tổng số học viên`
                : "0%"}
            </p>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-body-sm font-medium text-text-muted">
              Bài học đã xuất bản
            </CardTitle>
            <BookOpen className="size-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-display-sm font-bold text-success">{lessons.published}</div>
            <p className="text-caption text-text-muted mt-1">
              Trên tổng số {lessons.total} bài học
            </p>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-body-sm font-medium text-text-muted">
              Chờ kiểm duyệt
            </CardTitle>
            <Clock className="size-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-display-sm font-bold text-primary">{lessons.pending}</div>
            <p className="text-caption text-text-muted mt-1">Bài học cần phê duyệt</p>
          </CardContent>
        </Card>
      </div>

      {/* Analytics Breakdown Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Content Status Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-heading-sm">Trạng thái nội dung bài học</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-body-sm">
                <span className="flex items-center gap-1.5 text-text">
                  <CheckCircle2 className="size-4 text-success" /> Đã xuất bản
                </span>
                <span className="font-semibold text-text">
                  {lessons.published} bài ({publishedPercent}%)
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-2 overflow-hidden">
                <div
                  className="h-full bg-success rounded-full"
                  style={{ width: `${publishedPercent}%` }}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-body-sm">
                <span className="flex items-center gap-1.5 text-text">
                  <Clock className="size-4 text-warning" /> Đang chờ duyệt
                </span>
                <span className="font-semibold text-text">
                  {lessons.pending} bài ({pendingPercent}%){" "}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-2 overflow-hidden">
                <div
                  className="h-full bg-warning rounded-full"
                  style={{ width: `${pendingPercent}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
              <div className="rounded-lg bg-surface-2/40 p-3">
                <div className="flex items-center gap-1.5 text-caption text-text-muted mb-1">
                  <FileEdit className="size-3.5" /> Bản nháp (DRAFT)
                </div>
                <div className="text-heading-sm font-bold text-text">{lessons.draft} bài</div>
              </div>

              <div className="rounded-lg bg-surface-2/40 p-3">
                <div className="flex items-center gap-1.5 text-caption text-text-muted mb-1">
                  <XCircle className="size-3.5 text-danger" /> Bị từ chối
                </div>
                <div className="text-heading-sm font-bold text-danger">{lessons.rejected} bài</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions & Navigation */}
        <Card>
          <CardHeader>
            <CardTitle className="text-heading-sm">Lối tắt tác vụ quản trị</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link
              href="/admin/moderation"
              className="flex items-center justify-between p-3.5 rounded-lg border border-border hover:border-primary/50 hover:bg-surface-2/40 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="size-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                  <ShieldCheck className="size-5" />
                </div>
                <div>
                  <div className="text-body-sm font-semibold text-text group-hover:text-primary transition-colors">
                    Hàng đợi kiểm duyệt bài học
                  </div>
                  <div className="text-caption text-text-muted">
                    {lessons.pending > 0
                      ? `Có ${lessons.pending} bài học đang chờ phê duyệt`
                      : "Không có bài học nào đang chờ"}
                  </div>
                </div>
              </div>
              <ArrowRight className="size-4 text-text-muted group-hover:text-primary group-hover:translate-x-1 transition-all" />
            </Link>

            <Link
              href="/admin/lessons"
              className="flex items-center justify-between p-3.5 rounded-lg border border-border hover:border-primary/50 hover:bg-surface-2/40 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="size-9 rounded-lg bg-success/10 text-success flex items-center justify-center">
                  <BookOpen className="size-5" />
                </div>
                <div>
                  <div className="text-body-sm font-semibold text-text group-hover:text-primary transition-colors">
                    Soạn thảo & Quản lý bài học
                  </div>
                  <div className="text-caption text-text-muted">
                    Tạo mới, chỉnh sửa nội dung bài học DRAFT
                  </div>
                </div>
              </div>
              <ArrowRight className="size-4 text-text-muted group-hover:text-primary group-hover:translate-x-1 transition-all" />
            </Link>

            <Link
              href="/admin/categories"
              className="flex items-center justify-between p-3.5 rounded-lg border border-border hover:border-primary/50 hover:bg-surface-2/40 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="size-9 rounded-lg bg-info/10 text-info flex items-center justify-center">
                  <FolderTree className="size-5" />
                </div>
                <div>
                  <div className="text-body-sm font-semibold text-text group-hover:text-primary transition-colors">
                    Quản lý danh mục bài học
                  </div>
                  <div className="text-caption text-text-muted">
                    Tổng cộng {categories.total} danh mục chủ đề
                  </div>
                </div>
              </div>
              <ArrowRight className="size-4 text-text-muted group-hover:text-primary group-hover:translate-x-1 transition-all" />
            </Link>

            <Link
              href="/admin/users"
              className="flex items-center justify-between p-3.5 rounded-lg border border-border hover:border-primary/50 hover:bg-surface-2/40 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="size-9 rounded-lg bg-warning/10 text-warning flex items-center justify-center">
                  <UserCheck className="size-5" />
                </div>
                <div>
                  <div className="text-body-sm font-semibold text-text group-hover:text-primary transition-colors">
                    Quản lý học viên & Biên tập viên
                  </div>
                  <div className="text-caption text-text-muted">
                    Cấp VIP, khóa tài khoản, tạo Editor mới
                  </div>
                </div>
              </div>
              <ArrowRight className="size-4 text-text-muted group-hover:text-primary group-hover:translate-x-1 transition-all" />
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
