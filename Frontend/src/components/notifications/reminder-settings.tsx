"use client";

import * as React from "react";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { useNotificationSettings, useUpdateNotificationSettings } from "@/hooks/use-notifications";
import { useToast } from "@/hooks/use-toast";
import { errorMessageFor } from "@/lib/error-messages";
import { ClientApiError } from "@/lib/api-client";
import type { UpdateNotificationSettings } from "@/types/api";

const HOURS = Array.from({ length: 24 }, (_, h) => h);

// Only ever used while a request is in flight, never as a stand-in for
// settings we failed to load — see the error branch below.
const DEFAULT_ENABLED = true;
const DEFAULT_HOUR = 20;

export function ReminderSettings() {
  const { data: settings, isLoading, isError, refetch } = useNotificationSettings();
  const update = useUpdateNotificationSettings();
  const toast = useToast();

  // A pending edit, held only while its request is in flight. Reading from
  // the server answer the rest of the time means no second copy of the truth
  // to fall out of step — an effect that copied the response into state used
  // to flash the previous values for a frame after each save.
  const [draft, setDraft] = React.useState<UpdateNotificationSettings | null>(null);

  const current = draft ?? settings;
  const enabled = current?.enable_daily_reminder ?? DEFAULT_ENABLED;
  const hour = current?.reminder_hour ?? DEFAULT_HOUR;

  async function save(next: UpdateNotificationSettings) {
    setDraft(next);
    try {
      await update.mutateAsync(next);
      toast.success("Đã lưu cài đặt nhắc học.");
    } catch (err) {
      toast.error(err instanceof ClientApiError ? errorMessageFor(err.code) : "Đã có lỗi xảy ra.");
    } finally {
      // Either way the server answer takes over again: on success it already
      // holds `next`, on failure it still holds the old values — so the
      // screen never shows a setting that was not actually stored.
      setDraft(null);
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex justify-center py-8">
          <Spinner />
        </CardContent>
      </Card>
    );
  }

  // Never render defaults as if they were this user's settings: someone who
  // picked 07:00 would be shown 20:00 and reasonably believe that is what is
  // stored. Say the truth — we do not know yet — and offer a retry.
  if (isError || !settings) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-8 text-center">
          <AlertCircle className="size-6 text-danger" aria-hidden />
          <p className="text-body-sm text-text-muted">
            Không tải được cài đặt nhắc học. Cài đặt hiện tại của bạn vẫn được giữ nguyên.
          </p>
          <Button variant="outline" size="sm" onClick={() => void refetch()}>
            Thử lại
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Nhắc học hằng ngày</CardTitle>
        <CardDescription>
          Nếu hôm đó bạn chưa học bài nào, hệ thống sẽ nhắc bạn vào giờ bạn chọn — qua thông báo và
          email.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <Label htmlFor="reminder-enabled">Bật nhắc học</Label>
          <input
            id="reminder-enabled"
            type="checkbox"
            className="size-5 accent-[var(--color-primary)]"
            checked={enabled}
            disabled={update.isPending}
            onChange={(e) =>
              void save({ enable_daily_reminder: e.target.checked, reminder_hour: hour })
            }
          />
        </div>

        <div className="flex items-center justify-between gap-4">
          <Label htmlFor="reminder-hour">Giờ nhắc</Label>
          <select
            id="reminder-hour"
            className="h-10 rounded-md border border-border bg-background px-3 text-sm text-text disabled:opacity-50"
            value={hour}
            // Turning reminders off leaves the hour visible but inert —
            // clearer than hiding it, and the value is still there when the
            // user switches back on.
            disabled={!enabled || update.isPending}
            onChange={(e) =>
              void save({ enable_daily_reminder: enabled, reminder_hour: Number(e.target.value) })
            }
          >
            {HOURS.map((h) => (
              <option key={h} value={h}>
                {String(h).padStart(2, "0")}:00
              </option>
            ))}
          </select>
        </div>

        {update.isPending && (
          <p className="flex items-center gap-2 text-body-sm text-text-muted">
            <Spinner className="size-4" /> Đang lưu…
          </p>
        )}

        <p className="text-xs text-text-muted">
          Cài đặt này chỉ áp dụng cho nhắc học. Thông báo thanh toán, hết hạn VIP và tài khoản luôn
          được gửi.
        </p>
      </CardContent>
    </Card>
  );
}
