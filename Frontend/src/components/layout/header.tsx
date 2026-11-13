"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BookOpen, Crown, History, LogOut, ShieldCheck, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VipBadge } from "@/components/ui/badge";
import { Logo } from "@/components/layout/logo";
import { NotificationBell } from "@/components/layout/notification-bell";
import { cn } from "@/lib/utils";

export interface HeaderUser {
  fullName: string;
  isVip: boolean;
  role?: string;
}

export function Header({
  user,
}: {
  /** Omitted for a signed-out visitor. The home page is public, so the same
   * header has to work with no account behind it — one object rather than
   * several optional fields, so "signed in" can't be half-true. */
  user?: HeaderUser;
}) {
  const router = useRouter();
  const pathname = usePathname();

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  const isAdminOrEditor = user?.role === "ADMIN" || user?.role === "EDITOR";

  const navLinks = [
    { href: "/categories", label: "Bài học", icon: BookOpen },
    { href: "/history", label: "Tiến độ", icon: History },
    { href: "/profile", label: "Hồ sơ", icon: User },
    ...(isAdminOrEditor
      ? [{ href: "/moderation", label: "Kiểm duyệt", icon: ShieldCheck }]
      : []),
  ];

  return (
    <header className="sticky top-0 z-[var(--z-sticky)] border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-6 sm:gap-8">
          <Link href={user ? "/categories" : "/"}>
            <Logo compact />
          </Link>
          {user && (
            <nav className="flex items-center gap-1 sm:gap-2">
              {navLinks.map((item) => {
                const Icon = item.icon;
                const isActive = pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-body-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary/10 text-primary font-semibold"
                        : "text-text-muted hover:bg-surface-2 hover:text-text",
                    )}
                  >
                    <Icon className="size-4" aria-hidden />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          )}
        </div>

        {user ? (
          <div className="flex items-center gap-2 sm:gap-3">
            {user.isVip ? (
              <VipBadge />
            ) : (
              <Button asChild variant="secondary" size="sm" className="hidden sm:inline-flex">
                <Link href="/checkout">
                  <Crown className="size-3.5" aria-hidden />
                  Gói VIP
                </Link>
              </Button>
            )}
            <span className="hidden text-body-sm text-text-muted md:inline">{user.fullName}</span>
            <NotificationBell />
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="size-4" aria-hidden />
              <span className="hidden sm:inline">Đăng xuất</span>
            </Button>
          </div>
        ) : (
          // No bell here on purpose: with no account there is nothing to
          // notify, and a bell that always reads zero is just noise.
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm">
              <Link href="/login">Đăng nhập</Link>
            </Button>
            <Button asChild size="sm">
              <Link href="/register">Đăng ký</Link>
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}
