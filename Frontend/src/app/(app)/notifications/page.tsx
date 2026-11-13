"use client";

import * as React from "react";
import { BellOff, CheckCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { NotificationRow } from "@/components/notifications/notification-row";
import { ReminderSettings } from "@/components/notifications/reminder-settings";
import {
  PAGE_SIZE,
  useDeleteNotification,
  useMarkAllRead,
  useMarkRead,
  useNotifications,
} from "@/hooks/use-notifications";
import { useToast } from "@/hooks/use-toast";
import { errorMessageFor } from "@/lib/error-messages";
import { ClientApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";

export default function NotificationsPage() {
  const [page, setPage] = React.useState(1);
  const [unreadOnly, setUnreadOnly] = React.useState(false);
  const { data, isLoading, isFetching } = useNotifications({ page, unreadOnly });

  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();
  const remove = useDeleteNotification();
  const toast = useToast();

  // One entry per row currently mid-request, so each row shows its own
  // spinner. A single shared id was not enough: acting on row A and then row B
  // before A finished let A's `finally` clear B's lock, which both hid B's
  // spinner and re-opened its buttons for a second, duplicate request.
  const [busyIds, setBusyIds] = React.useState<ReadonlySet<string>>(new Set());

  function reportError(err: unknown) {
    toast.error(err instanceof ClientApiError ? errorMessageFor(err.code) : "Đã có lỗi xảy ra.");
  }

  /** Runs `action` with the row locked, ignoring repeat clicks while it is
   * in flight. Returns without acting if the row is already busy. */
  async function withRowLock(id: string, action: () => Promise<void>) {
    if (busyIds.has(id)) return;
    setBusyIds((prev) => new Set(prev).add(id));
    try {
      await action();
    } catch (err) {
      reportError(err);
    } finally {
      setBusyIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  }

  function handleMarkRead(id: string) {
    void withRowLock(id, async () => {
      await markRead.mutateAsync(id);
    });
  }

  function handleDelete(id: string) {
    void withRowLock(id, async () => {
      await remove.mutateAsync(id);
      toast.success("Đã xoá thông báo.");
    });
  }

  async function handleMarkAllRead() {
    try {
      const { updated } = await markAllRead.mutateAsync();
      toast.success(updated > 0 ? `Đã đánh dấu ${updated} thông báo.` : "Không có gì chưa đọc.");
    } catch (err) {
      reportError(err);
    }
  }

  const items = data?.items ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  // Deleting the last row of the last page leaves `page` pointing past the
  // end: an empty list, and the pager hidden because totalPages dropped to 1
  // — no way back except reloading the browser. Follow the list back in.
  React.useEffect(() => {
    if (data && page > totalPages) setPage(totalPages);
  }, [data, page, totalPages]);

  function changeFilter(next: boolean) {
    setUnreadOnly(next);
    // Page 3 of the full list is usually past the end of the unread one,
    // which would land the user on an empty list they did not ask for.
    setPage(1);
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-h1 text-text">Thông báo</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={handleMarkAllRead}
          loading={markAllRead.isPending}
          disabled={!data || data.unread_count === 0}
        >
          <CheckCheck className="size-4" aria-hidden />
          Đánh dấu đã đọc tất cả
        </Button>
      </div>

      <div className="flex gap-2" role="group" aria-label="Lọc thông báo">
        {[
          { label: "Tất cả", value: false },
          { label: `Chưa đọc${data ? ` (${data.unread_count})` : ""}`, value: true },
        ].map((tab) => (
          <Button
            key={tab.label}
            size="sm"
            variant={unreadOnly === tab.value ? "primary" : "ghost"}
            aria-pressed={unreadOnly === tab.value}
            onClick={() => changeFilter(tab.value)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      <Card>
        {isLoading ? (
          <CardContent className="flex justify-center py-12">
            <Spinner />
          </CardContent>
        ) : items.length === 0 ? (
          <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
            <BellOff className="size-8 text-text-muted" aria-hidden />
            <p className="text-body text-text-muted">
              {unreadOnly ? "Bạn đã đọc hết thông báo." : "Chưa có thông báo nào."}
            </p>
          </CardContent>
        ) : (
          <ul className={cn("transition-opacity", isFetching && "opacity-60")}>
            {items.map((item) => (
              <NotificationRow
                key={item.id}
                item={item}
                busy={busyIds.has(item.id)}
                onMarkRead={handleMarkRead}
                onDelete={handleDelete}
              />
            ))}
          </ul>
        )}
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1 || isFetching}
            onClick={() => setPage((p) => p - 1)}
          >
            Trước
          </Button>
          <span className="text-body-sm text-text-muted">
            Trang {page}/{totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages || isFetching}
            onClick={() => setPage((p) => p + 1)}
          >
            Sau
          </Button>
        </div>
      )}

      <ReminderSettings />
    </div>
  );
}
