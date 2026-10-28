"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VipBadge } from "@/components/ui/badge";

export function Header({ fullName, isVip }: { fullName: string; isVip: boolean }) {
  const router = useRouter();

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="border-b border-border bg-background">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/profile" className="text-lg font-semibold text-text">
          PBL6
        </Link>
        <div className="flex items-center gap-3">
          {isVip && <VipBadge />}
          <span className="text-sm text-text-muted">{fullName}</span>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="size-4" aria-hidden />
            Đăng xuất
          </Button>
        </div>
      </div>
    </header>
  );
}
