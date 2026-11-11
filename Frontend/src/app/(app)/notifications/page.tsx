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

  // Which row is mid-request, so only that row shows a spinner instead of
  // the whole list freezing.
  const [busyId, setBusyId] = React.useState<string | null>(null);

  function reportError(err: unknown) {
    toast.error(err instanceof ClientApiError ? errorMessageFor(err.code) : "Đã có lỗi xảy ra.");
  }

  async function handleMarkRead(id: string) {
    setBusyId(id);
    try {
      await markRead.mutateAsync(id);
    } catch (err) {
      reportError(err);
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(id: string) {
    setBusyId(id);
    try {
      await remove.mutateAsync(id);
      toast.success("Đã xoá thông báo.");
    } catch (err) {
      reportError(err);
    } finally {
      setBusyId(null);
    }
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

  function changeFilter(next: boolean) {
    setUnreadOnly(next);
    // Page 3 of "tất cả" is usually past the end of "chưa đọc", which would
    // land the user on an empty list they did not ask for.
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
                busy={busyId === item.id}
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
