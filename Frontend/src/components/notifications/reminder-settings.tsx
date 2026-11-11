"use client";

import * as React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { useNotificationSettings, useUpdateNotificationSettings } from "@/hooks/use-notifications";
import { useToast } from "@/hooks/use-toast";
import { errorMessageFor } from "@/lib/error-messages";
import { ClientApiError } from "@/lib/api-client";

const HOURS = Array.from({ length: 24 }, (_, h) => h);

export function ReminderSettings() {
  const { data: settings, isLoading } = useNotificationSettings();
  const update = useUpdateNotificationSettings();
  const toast = useToast();

  // Local copies so the switch and the select respond instantly; the server
  // answer is the source of truth once it arrives.
  const [enabled, setEnabled] = React.useState(true);
  const [hour, setHour] = React.useState(20);

  React.useEffect(() => {
    if (settings) {
      setEnabled(settings.enable_daily_reminder);
      setHour(settings.reminder_hour);
    }
  }, [settings]);

  async function save(next: { enable_daily_reminder: boolean; reminder_hour: number }) {
    try {
      await update.mutateAsync(next);
      toast.success("Đã lưu cài đặt nhắc học.");
    } catch (err) {
      toast.error(err instanceof ClientApiError ? errorMessageFor(err.code) : "Đã có lỗi xảy ra.");
      // Put the controls back where the server says they are, so the screen
      // never shows a setting that was not actually stored.
      if (settings) {
        setEnabled(settings.enable_daily_reminder);
        setHour(settings.reminder_hour);
      }
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
            onChange={(e) => {
              setEnabled(e.target.checked);
              void save({ enable_daily_reminder: e.target.checked, reminder_hour: hour });
            }}
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
            onChange={(e) => {
              const next = Number(e.target.value);
              setHour(next);
              void save({ enable_daily_reminder: enabled, reminder_hour: next });
            }}
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
