"use client";

import { useState } from "react";
import { FolderTree, Plus, Pencil, Trash2, Loader2, X } from "lucide-react";
import {
  useAdminCategories,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
} from "@/hooks/use-admin-categories";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import type { CategoryTreeResponse } from "@/types/content";

function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[đĐ]/g, "d")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)+/g, "");
}

export default function AdminCategoriesPage() {
  const { data: categories = [], isLoading } = useAdminCategories();
  const createMutation = useCreateCategory();
  const updateMutation = useUpdateCategory();
  const deleteMutation = useDeleteCategory();
  const { success, error } = useToast();

  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCat, setEditingCat] = useState<CategoryTreeResponse | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [sortOrder, setSortOrder] = useState(0);

  function openCreateModal() {
    setEditingCat(null);
    setName("");
    setSlug("");
    setSortOrder(0);
    setIsModalOpen(true);
  }

  function openEditModal(cat: CategoryTreeResponse) {
    setEditingCat(cat);
    setName(cat.name);
    setSlug(cat.slug);
    setSortOrder(cat.sort_order ?? 0);
    setIsModalOpen(true);
  }

  function handleNameChange(val: string) {
    setName(val);
    if (!editingCat) {
      setSlug(slugify(val));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      error("Tên danh mục không được để trống.");
      return;
    }

    try {
      if (editingCat) {
        await updateMutation.mutateAsync({
          id: editingCat.id,
          name: name.trim(),
          slug: slug.trim() || slugify(name),
          sort_order: Number(sortOrder) || 0,
        });
        success("Đã cập nhật danh mục thành công!");
      } else {
        await createMutation.mutateAsync({
          name: name.trim(),
          slug: slug.trim() || slugify(name),
          sort_order: Number(sortOrder) || 0,
        });
        success("Đã tạo danh mục mới thành công!");
      }
      setIsModalOpen(false);
    } catch {
      error("Có lỗi xảy ra khi lưu danh mục.");
    }
  }

  async function handleDelete(cat: CategoryTreeResponse) {
    if (!confirm(`Bạn có chắc chắn muốn xóa danh mục "${cat.name}"?`)) {
      return;
    }
    try {
      await deleteMutation.mutateAsync(cat.id);
      success("Đã xóa danh mục thành công.");
    } catch {
      error("Không thể xóa danh mục này (có thể đang chứa bài học).");
    }
  }

  const filtered = categories.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.slug.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-display-sm font-bold text-text flex items-center gap-2">
            <FolderTree className="size-6 text-primary" />
            Quản lý danh mục
          </h1>
          <p className="text-body-sm text-text-muted mt-1">
            Phân loại các chủ đề và danh mục bài học tiếng Anh cho toàn hệ thống.
          </p>
        </div>
        <Button variant="primary" onClick={openCreateModal}>
          <Plus className="size-4 mr-1.5" />
          Thêm danh mục
        </Button>
      </div>

      {/* Table Card */}
      <Card>
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-heading-sm">Danh sách danh mục</CardTitle>
          <div className="w-full sm:w-64">
            <Input
              type="text"
              placeholder="Tìm theo tên hoặc slug..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 text-text-muted">
              <Loader2 className="size-8 animate-spin mb-3 text-primary" />
              <p>Đang tải danh mục...</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center text-text-muted">
              <p>Chưa có danh mục nào hoặc không tìm thấy kết quả phù hợp.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-body-sm">
                <thead className="border-b border-border bg-surface-2/50 text-caption font-semibold text-text-muted uppercase">
                  <tr>
                    <th className="px-4 py-3">Tên danh mục</th>
                    <th className="px-4 py-3">Slug</th>
                    <th className="px-4 py-3 text-center">Thứ tự</th>
                    <th className="px-4 py-3 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filtered.map((cat) => (
                    <tr key={cat.id} className="hover:bg-surface-2/30 transition-colors">
                      <td className="px-4 py-3 font-medium text-text">{cat.name}</td>
                      <td className="px-4 py-3 font-mono text-caption text-text-muted">
                        {cat.slug}
                      </td>
                      <td className="px-4 py-3 text-center text-text-muted">
                        {cat.sort_order ?? 0}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button variant="ghost" size="sm" onClick={() => openEditModal(cat)}>
                            <Pencil className="size-3.5 mr-1" />
                            Sửa
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-danger hover:bg-danger/10 hover:text-danger"
                            onClick={() => handleDelete(cat)}
                          >
                            <Trash2 className="size-3.5 mr-1" />
                            Xóa
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

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-border bg-background p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-heading-sm font-bold text-text">
                {editingCat ? "Chỉnh sửa danh mục" : "Tạo danh mục mới"}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => setIsModalOpen(false)}>
                <X className="size-5" />
              </Button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-body-sm font-medium text-text mb-1">
                  Tên danh mục <span className="text-danger">*</span>
                </label>
                <Input
                  type="text"
                  placeholder="VD: Ngữ pháp tiếng Anh"
                  value={name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-body-sm font-medium text-text mb-1">
                  Slug (URL-friendly)
                </label>
                <Input
                  type="text"
                  placeholder="VD: ngu-phap-tieng-anh"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-body-sm font-medium text-text mb-1">
                  Thứ tự hiển thị
                </label>
                <Input
                  type="number"
                  value={sortOrder}
                  onChange={(e) => setSortOrder(Number(e.target.value))}
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
                  {editingCat ? "Cập nhật" : "Tạo mới"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
