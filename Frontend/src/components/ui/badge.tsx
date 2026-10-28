import * as React from "react";
import { Crown } from "lucide-react";
import { cn } from "@/lib/utils";

const VARIANT_CLASSES: Record<string, string> = {
  neutral: "bg-surface-2 text-text-muted",
  success: "bg-success/10 text-success",
  danger: "bg-danger/10 text-danger",
  warning: "bg-warning/10 text-warning",
  info: "bg-info/10 text-info",
};

export function Badge({
  className,
  variant = "neutral",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof VARIANT_CLASSES }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        VARIANT_CLASSES[variant],
        className,
      )}
      {...props}
    />
  );
}

// design-system.md §8: "VIP badge = secondary gradient + crown icon, not a
// plain badge."
export function VipBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold text-secondary-foreground",
        "bg-gradient-to-r from-secondary to-amber-300",
        className,
      )}
    >
      <Crown className="size-3.5" aria-hidden />
      VIP
    </span>
  );
}
