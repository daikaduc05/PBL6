"use client";

import { useState } from "react";
import {
  Users,
  UserCheck,
  Lock,
  Unlock,
  Crown,
  Plus,
  Loader2,
  X,
  Mail,
  ShieldAlert,
} from "lucide-react";
import {
  useAdminStudents,
  useAdminEditors,
  useUpdateUserStatus,
  useUpdateUserVip,
  useCreateEditor,
} from "@/hooks/use-admin-users";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge, VipBadge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import type { UserProfile } from "@/types/api";

export default function AdminUsersPage() {
  const [activeTab, setActiveTab] = useState<"students" | "editors">("students");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const { data: studentsData, isLoading: isLoadingStudents } = useAdminStudents({
    q: search || undefined,
    status: statusFilter,
  });
  const { data: editors = [], isLoading: isLoadingEditors } = useAdminEditors();

  const updateStatusMutation = useUpdateUserStatus();
  const updateVipMutation = useUpdateUserVip();
  const createEditorMutation = useCreateEditor();
  const { success, error } = useToast();

  // Modals
  const [statusModalUser, setStatusModalUser] = useState<UserProfile | null>(null);
  const [lockReason, setLockReason] = useState("");

  const [vipModalUser, setVipModalUser] = useState<UserProfile | null>(null);

  const [isEditorModalOpen, setIsEditorModalOpen] = useState(false);
  const [editorName, setEditorName] = useState("");
  const [editorEmail, setEditorEmail] = useState("");
  const [editorPassword, setEditorPassword] = useState("");

  const students = studentsData?.items || [];

  async function handleToggleStatus() {
    if (!statusModalUser) return;
    const isCurrentlyLocked = statusModalUser.status === "LOCKED";
    const newStatus = isCurrentlyLocked ? "ACTIVE" : "LOCKED";

    try {
      await updateStatusMutation.mutateAsync({
        userId: statusModalUser.id,
        status: newStatus,
        reason: isCurrentlyLocked ? undefined : lockReason.trim() || undefined,
      });
      success(
        isCurrentlyLocked
          ? `Đã mở khóa tài khoản ${statusModalUser.full_name}!`
          : `Đã khóa tài khoản ${statusModalUser.full_name}!`,
      );
      setStatusModalUser(null);
      setLockReason("");
    } catch {
      error("Có lỗi xảy ra khi cập nhật trạng thái tài khoản.");
    }
  }

  async function handleToggleVip() {
    if (!vipModalUser) return;
    const willBeVip = !vipModalUser.is_vip;

    try {
      await updateVipMutation.mutateAsync({
        userId: vipModalUser.id,
        isVip: willBeVip,
        vipExpiredAt: willBeVip
          ? new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
          : null,
      });
      success(
        willBeVip
          ? `Đã cấp VIP thành công cho ${vipModalUser.full_name}!`
          : `Đã thu hồi gói VIP của ${vipModalUser.full_name}!`,
      );
      setVipModalUser(null);
    } catch {
      error("Có lỗi xảy ra khi cập nhật gói VIP.");
    }
  }

  async function handleCreateEditor(e: React.FormEvent) {
    e.preventDefault();
    if (!editorEmail.trim() || !editorName.trim()) {
      error("Vui lòng điền đầy đủ họ tên và email.");
      return;
    }

    try {
      await createEditorMutation.mutateAsync({
        full_name: editorName.trim(),
        email: editorEmail.trim(),
        password: editorPassword || "Editor@123456",
      });
      success("Đã tạo tài khoản Biên tập viên (Editor) mới thành công!");
      setIsEditorModalOpen(false);
      setEditorName("");
      setEditorEmail("");
      setEditorPassword("");
    } catch {
      error("Có lỗi xảy ra khi tạo tài khoản Editor.");
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-display-sm font-bold text-text flex items-center gap-2">
            <Users className="size-6 text-primary" />
            Quản trị người dùng
          </h1>
          <p className="text-body-sm text-text-muted mt-1">
            Quản lý tài khoản học viên, điều chỉnh trạng thái và cấp quyền cho đội ngũ biên tập.
          </p>
        </div>
        {activeTab === "editors" && (
          <Button variant="primary" onClick={() => setIsEditorModalOpen(true)}>
            <Plus className="size-4 mr-1.5" />
            Tạo Editor mới
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        <button
          onClick={() => setActiveTab("students")}
          className={`flex items-center gap-2 px-5 py-3 text-body-sm font-semibold transition-colors border-b-2 ${
            activeTab === "students"
              ? "border-primary text-primary"
              : "border-transparent text-text-muted hover:text-text"
          }`}
        >
          <UserCheck className="size-4" />
          Học viên ({students.length})
        </button>
        <button
          onClick={() => setActiveTab("editors")}
          className={`flex items-center gap-2 px-5 py-3 text-body-sm font-semibold transition-colors border-b-2 ${
            activeTab === "editors"
              ? "border-primary text-primary"
              : "border-transparent text-text-muted hover:text-text"
          }`}
        >
          <ShieldAlert className="size-4" />
          Biên tập viên (Editor) ({editors.length})
        </button>
      </div>

      {/* Students Tab Content */}
      {activeTab === "students" && (
        <Card>
          <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="text-heading-sm">Danh sách học viên</CardTitle>
            <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
              <div className="w-full sm:w-64">
                <Input
                  type="text"
                  placeholder="Tìm theo tên hoặc email..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-body-sm text-text focus:border-primary focus:outline-none"
                >
                  <option value="all">Tất cả trạng thái</option>
                  <option value="ACTIVE">Hoạt động</option>
                  <option value="LOCKED">Đã khóa</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoadingStudents ? (
              <div className="flex flex-col items-center justify-center py-12 text-text-muted">
                <Loader2 className="size-8 animate-spin mb-3 text-primary" />
                <p>Đang tải danh sách học viên...</p>
              </div>
            ) : students.length === 0 ? (
              <div className="py-12 text-center text-text-muted">
                <p>Không tìm thấy học viên nào phù hợp.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-body-sm">
                  <thead className="border-b border-border bg-surface-2/50 text-caption font-semibold text-text-muted uppercase">
                    <tr>
                      <th className="px-4 py-3">Học viên</th>
                      <th className="px-4 py-3">Gói</th>
                      <th className="px-4 py-3">Trạng thái</th>
                      <th className="px-4 py-3">Ngày tham gia</th>
                      <th className="px-4 py-3 text-right">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {students.map((student) => {
                      const isLocked = student.status === "LOCKED";
                      return (
                        <tr key={student.id} className="hover:bg-surface-2/30 transition-colors">
                          <td className="px-4 py-3">
                            <div className="font-medium text-text">{student.full_name}</div>
                            <div className="flex items-center gap-1 text-caption text-text-muted">
                              <Mail className="size-3" />
                              {student.email}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            {student.is_vip ? (
                              <VipBadge />
                            ) : (
                              <span className="text-caption text-text-muted font-medium">
                                Thường
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {isLocked ? (
                              <Badge variant="danger" className="gap-1">
                                <Lock className="size-3" /> Đã khóa
                              </Badge>
                            ) : (
                              <Badge variant="success" className="gap-1">
                                <UserCheck className="size-3" /> Hoạt động
                              </Badge>
                            )}
                          </td>
                          <td className="px-4 py-3 text-text-muted">
                            {new Date(student.created_at).toLocaleDateString("vi-VN")}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                className={student.is_vip ? "text-warning" : "text-primary"}
                                onClick={() => setVipModalUser(student)}
                              >
                                <Crown className="size-3.5 mr-1" />
                                {student.is_vip ? "Hủy VIP" : "Cấp VIP"}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className={
                                  isLocked
                                    ? "text-success hover:bg-success/10"
                                    : "text-danger hover:bg-danger/10"
                                }
                                onClick={() => setStatusModalUser(student)}
                              >
                                {isLocked ? (
                                  <>
                                    <Unlock className="size-3.5 mr-1" /> Mở khóa
                                  </>
                                ) : (
                                  <>
                                    <Lock className="size-3.5 mr-1" /> Khóa
                                  </>
                                )}
                              </Button>
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
      )}

      {/* Editors Tab Content */}
      {activeTab === "editors" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-heading-sm">
              Đội ngũ biên tập viên (Editor) ({editors.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingEditors ? (
              <div className="flex flex-col items-center justify-center py-12 text-text-muted">
                <Loader2 className="size-8 animate-spin mb-3 text-primary" />
                <p>Đang tải danh sách biên tập viên...</p>
              </div>
            ) : editors.length === 0 ? (
              <div className="py-12 text-center text-text-muted">
                <p>Chưa có biên tập viên nào. Bấm &quot;Tạo Editor mới&quot; để thêm.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-body-sm">
                  <thead className="border-b border-border bg-surface-2/50 text-caption font-semibold text-text-muted uppercase">
                    <tr>
                      <th className="px-4 py-3">Biên tập viên</th>
                      <th className="px-4 py-3">Vai trò</th>
                      <th className="px-4 py-3">Trạng thái</th>
                      <th className="px-4 py-3">Ngày tạo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {editors.map((editor) => (
                      <tr key={editor.id} className="hover:bg-surface-2/30 transition-colors">
                        <td className="px-4 py-3">
                          <div className="font-medium text-text">{editor.full_name}</div>
                          <div className="flex items-center gap-1 text-caption text-text-muted">
                            <Mail className="size-3" />
                            {editor.email}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="info">EDITOR</Badge>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="success">Hoạt động</Badge>
                        </td>
                        <td className="px-4 py-3 text-text-muted">
                          {new Date(editor.created_at).toLocaleDateString("vi-VN")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Lock/Unlock Modal */}
      {statusModalUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-border bg-background p-6 shadow-xl space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-heading-sm font-bold text-text">
                  {statusModalUser.status === "LOCKED"
                    ? "Xác nhận mở khóa tài khoản"
                    : "Xác nhận khóa tài khoản"}
                </h3>
                <p className="text-body-sm text-text-muted mt-1">
                  Người dùng: <span className="font-semibold">{statusModalUser.full_name}</span> (
                  {statusModalUser.email})
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setStatusModalUser(null)}>
                <X className="size-4" />
              </Button>
            </div>

            {statusModalUser.status !== "LOCKED" && (
              <div>
                <label className="block text-body-sm font-medium text-text mb-1">
                  Lý do khóa tài khoản (tùy chọn)
                </label>
                <textarea
                  rows={2}
                  placeholder="VD: Vi phạm quy chuẩn bình luận..."
                  value={lockReason}
                  onChange={(e) => setLockReason(e.target.value)}
                  className="w-full rounded-md border border-border bg-surface-1 p-2.5 text-body-sm text-text focus:border-primary focus:outline-none"
                />
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setStatusModalUser(null)}>
                Hủy
              </Button>
              <Button
                variant={statusModalUser.status === "LOCKED" ? "primary" : "destructive"}
                onClick={handleToggleStatus}
                disabled={updateStatusMutation.isPending}
              >
                {updateStatusMutation.isPending && (
                  <Loader2 className="size-4 animate-spin mr-1.5" />
                )}
                {statusModalUser.status === "LOCKED" ? "Mở khóa ngay" : "Khóa tài khoản"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* VIP Modal */}
      {vipModalUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-border bg-background p-6 shadow-xl space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-heading-sm font-bold text-text">
                  {vipModalUser.is_vip ? "Thu hồi quyền VIP" : "Cấp quyền VIP thủ công"}
                </h3>
                <p className="text-body-sm text-text-muted mt-1">
                  Người dùng: <span className="font-semibold">{vipModalUser.full_name}</span>
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setVipModalUser(null)}>
                <X className="size-4" />
              </Button>
            </div>

            <p className="text-body-sm text-text-muted">
              {vipModalUser.is_vip
                ? "Tài khoản này sẽ trở về trạng thái học viên thường và không thể truy cập các bài học VIP."
                : "Học viên sẽ được cấp 30 ngày quyền truy cập toàn bộ bài học và tính năng VIP mà không cần nạp tiền."}
            </p>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setVipModalUser(null)}>
                Hủy
              </Button>
              <Button
                variant={vipModalUser.is_vip ? "destructive" : "primary"}
                onClick={handleToggleVip}
                disabled={updateVipMutation.isPending}
              >
                {updateVipMutation.isPending && <Loader2 className="size-4 animate-spin mr-1.5" />}
                {vipModalUser.is_vip ? "Xác nhận thu hồi" : "Xác nhận cấp VIP (30 ngày)"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Create Editor Modal */}
      {isEditorModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-border bg-background p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-heading-sm font-bold text-text">
                Thêm Biên tập viên mới (Editor)
              </h3>
              <Button variant="ghost" size="sm" onClick={() => setIsEditorModalOpen(false)}>
                <X className="size-5" />
              </Button>
            </div>

            <form onSubmit={handleCreateEditor} className="space-y-4">
              <div>
                <label className="block text-body-sm font-medium text-text mb-1">
                  Họ và tên <span className="text-danger">*</span>
                </label>
                <Input
                  type="text"
                  placeholder="VD: Nguyễn Văn Biên Tập"
                  value={editorName}
                  onChange={(e) => setEditorName(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-body-sm font-medium text-text mb-1">
                  Email đăng nhập <span className="text-danger">*</span>
                </label>
                <Input
                  type="email"
                  placeholder="VD: editor@domain.com"
                  value={editorEmail}
                  onChange={(e) => setEditorEmail(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-body-sm font-medium text-text mb-1">
                  Mật khẩu ban đầu
                </label>
                <Input
                  type="password"
                  placeholder="Mặc định: Editor@123456"
                  value={editorPassword}
                  onChange={(e) => setEditorPassword(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-border">
                <Button type="button" variant="outline" onClick={() => setIsEditorModalOpen(false)}>
                  Hủy
                </Button>
                <Button type="submit" variant="primary" disabled={createEditorMutation.isPending}>
                  {createEditorMutation.isPending && (
                    <Loader2 className="size-4 animate-spin mr-1.5" />
                  )}
                  Tạo Editor
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
