"use client";

import Link from "next/link";
import { Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUnreadCount } from "@/hooks/use-notifications";

/** Split out of Header so the query lives in a component that only renders
 * for a signed-in user — Header itself is also used on the public home page,
 * where asking /api/notifications would just earn a 401 on every visit. */
export function NotificationBell() {
  const { data: unreadCount = 0 } = useUnreadCount();

  return (
    <Button asChild variant="ghost" size="sm" aria-label="Thông báo">
      <Link href="/notifications" className="relative">
        <Bell className="size-4" aria-hidden />
        {unreadCount > 0 && (
          <span
            aria-label={`${unreadCount} thông báo chưa đọc`}
            className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-1 text-[10px] font-semibold leading-none text-danger-foreground"
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </Link>
    </Button>
  );
}
