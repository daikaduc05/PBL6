import { GraduationCap } from "lucide-react";
import { cn } from "@/lib/utils";

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <div className={cn("inline-flex items-center gap-2", className)}>
      <span
        className={cn(
          "flex items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary-hover text-primary-foreground shadow-primary",
          compact ? "size-8" : "size-9",
        )}
      >
        <GraduationCap className={compact ? "size-4" : "size-5"} aria-hidden />
      </span>
      <span
        className={cn(
          "whitespace-nowrap font-semibold text-text",
          compact ? "text-sm sm:text-base" : "text-h3",
        )}
      >
        English Self-Study
      </span>
    </div>
  );
}
