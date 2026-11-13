"use client";

import { Bell, BookOpen, CreditCard, Lock, LockOpen, Trash2, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { cn, formatDate } from "@/lib/utils";
import type { NotificationItem, NotificationType } from "@/types/api";

// Keyed on `type`, never on `title`: the title is display copy the backend
// may reword at any time, and an icon rule matching its text would break
// silently when it does. That is exactly why the type column exists.
const ICONS: Record<NotificationType, LucideIcon> = {
  STUDY_REMINDER: Bell,
  PAYMENT_SUCCEEDED: CreditCard,
  VIP_EXPIRED: CreditCard,
  ACCOUNT_LOCKED: Lock,
  ACCOUNT_UNLOCKED: LockOpen,
  LESSON_PUBLISHED: BookOpen,
};

const ICON_TONES: Record<NotificationType, string> = {
  STUDY_REMINDER: "text-primary",
  PAYMENT_SUCCEEDED: "text-success",
  VIP_EXPIRED: "text-warning",
  ACCOUNT_LOCKED: "text-danger",
  ACCOUNT_UNLOCKED: "text-success",
  LESSON_PUBLISHED: "text-info",
};

/** Time-of-day matters for a study reminder ("đã đến giờ học"), so this
 * shows the clock as well — formatDate alone would render every reminder in
 * a day as the same string. */
function formatWhen(iso: string): string {
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mm} ${formatDate(iso)}`;
}

export function NotificationRow({
  item,
  onMarkRead,
  onDelete,
  busy = false,
}: {
  item: NotificationItem;
  onMarkRead: (id: string) => void;
  onDelete: (id: string) => void;
  busy?: boolean;
}) {
  const Icon = ICONS[item.type] ?? Bell;
  const tone = ICON_TONES[item.type] ?? "text-text-muted";

  return (
    <li
      className={cn(
        "flex gap-3 border-b border-border p-4 last:border-b-0",
        !item.is_read && "bg-surface-2/50",
      )}
    >
      <Icon className={cn("mt-0.5 size-5 shrink-0", tone)} aria-hidden />

      <div className="min-w-0 flex-1">
        <div className="flex items-start gap-2">
          <h3 className={cn("text-body text-text", !item.is_read && "font-semibold")}>
            {item.title}
          </h3>
          {!item.is_read && (
            <span
              className="mt-1.5 size-2 shrink-0 rounded-full bg-primary"
              aria-label="Chưa đọc"
            />
          )}
        </div>
        <p className="mt-1 text-body-sm text-text-muted">{item.content}</p>
        <time className="mt-2 block text-xs text-text-muted" dateTime={item.created_at}>
          {formatWhen(item.created_at)}
        </time>
      </div>

      <div className="flex shrink-0 items-start gap-1">
        {busy ? (
          <Spinner className="size-4" />
        ) : (
          <>
            {!item.is_read && (
              <Button variant="ghost" size="sm" onClick={() => onMarkRead(item.id)}>
                Đã đọc
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              aria-label={`Xoá thông báo: ${item.title}`}
              onClick={() => onDelete(item.id)}
            >
              <Trash2 className="size-4" aria-hidden />
            </Button>
          </>
        )}
      </div>
    </li>
  );
}
