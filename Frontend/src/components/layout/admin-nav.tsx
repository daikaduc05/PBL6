"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ShieldCheck, BookOpen, FolderTree, Users } from "lucide-react";
import { cn } from "@/lib/utils";

export function AdminNav({ role }: { role: string }) {
  const pathname = usePathname();
  const isAdmin = role.toUpperCase() === "ADMIN";

  const tabs = [
    { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/admin/moderation", label: "Kiểm duyệt", icon: ShieldCheck },
    { href: "/admin/lessons", label: "Bài học", icon: BookOpen },
    { href: "/admin/categories", label: "Danh mục", icon: FolderTree },
    ...(isAdmin ? [{ href: "/admin/users", label: "Người dùng", icon: Users }] : []),
  ];

  return (
    <nav className="mb-6 flex overflow-x-auto border-b border-border bg-surface-1/50 p-1.5 rounded-xl">
      <div className="flex gap-1.5">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive =
            pathname === tab.href ||
            (tab.href !== "/admin/dashboard" && pathname.startsWith(tab.href));

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "flex items-center gap-2 rounded-lg px-3.5 py-2 text-body-sm font-medium transition-all whitespace-nowrap",
                isActive
                  ? "bg-primary text-white font-semibold shadow-sm"
                  : "text-text-muted hover:bg-surface-2 hover:text-text",
              )}
            >
              <Icon className="size-4" />
              <span>{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
