"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VipBadge } from "@/components/ui/badge";
import { Logo } from "@/components/layout/logo";
import { NotificationBell } from "@/components/layout/notification-bell";

export interface HeaderUser {
  fullName: string;
  isVip: boolean;
}

export function Header({
  user,
}: {
  /** Omitted for a signed-out visitor. The home page is public, so the same
   * header has to work with no account behind it — one object rather than two
   * optional fields, so "signed in" can't be half-true. */
  user?: HeaderUser;
}) {
  const router = useRouter();

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-[var(--z-sticky)] border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/">
          <Logo compact />
        </Link>

        {user ? (
          <div className="flex items-center gap-3">
            {user.isVip && <VipBadge />}
            <span className="hidden text-body-sm text-text-muted sm:inline">{user.fullName}</span>
            <NotificationBell />
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="size-4" aria-hidden />
              Đăng xuất
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
