"use client";

import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from "lucide-react";
import { useToastStore, type ToastVariant } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const VARIANT_STYLES: Record<ToastVariant, { icon: typeof Info; classes: string }> = {
  success: { icon: CheckCircle2, classes: "border-success/30 bg-success/10 text-success" },
  danger: { icon: AlertCircle, classes: "border-danger/30 bg-danger/10 text-danger" },
  warning: { icon: AlertTriangle, classes: "border-warning/30 bg-warning/10 text-warning" },
  info: { icon: Info, classes: "border-info/30 bg-info/10 text-info" },
};

export function Toaster() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);

  return (
    <div className="fixed bottom-4 right-4 z-[var(--z-toast)] flex w-full max-w-sm flex-col gap-2">
      {toasts.map((t) => {
        const { icon: Icon, classes } = VARIANT_STYLES[t.variant];
        return (
          <div
            key={t.id}
            role="status"
            className={cn(
              "flex items-start gap-2 rounded-md border px-4 py-3 text-sm shadow-md",
              "bg-background",
              classes,
            )}
          >
            <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
            <p className="flex-1 text-text">{t.title}</p>
            <button
              onClick={() => dismiss(t.id)}
              aria-label="Đóng thông báo"
              className="text-text-muted hover:text-text"
            >
              <X className="size-4" aria-hidden />
            </button>
          </div>
        );
      })}
    </div>
  );
}
