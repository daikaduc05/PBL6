"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VipBadge } from "@/components/ui/badge";
import { Logo } from "@/components/layout/logo";

export function Header({ fullName, isVip }: { fullName: string; isVip: boolean }) {
  const router = useRouter();

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-[var(--z-sticky)] border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/profile">
          <Logo compact />
        </Link>
        <div className="flex items-center gap-3">
          {isVip && <VipBadge />}
          <span className="hidden text-body-sm text-text-muted sm:inline">{fullName}</span>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="size-4" aria-hidden />
            Đăng xuất
          </Button>
        </div>
      </div>
    </header>
  );
}
