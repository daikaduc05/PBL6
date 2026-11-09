import { cn } from "@/lib/utils";
import type { LessonLevel } from "@/types/content";

export interface LevelFilterProps {
  value: LessonLevel | "all";
  onChange: (level: LessonLevel | "all") => void;
  className?: string;
}

const LEVELS: { key: LessonLevel | "all"; label: string }[] = [
  { key: "all", label: "Tất cả cấp độ" },
  { key: "easy", label: "Cơ bản" },
  { key: "medium", label: "Trung bình" },
  { key: "hard", label: "Nâng cao" },
];

export function LevelFilter({ value, onChange, className }: LevelFilterProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-1.5", className)}>
      {LEVELS.map((lvl) => {
        const isActive = value === lvl.key;
        return (
          <button
            key={lvl.key}
            type="button"
            onClick={() => onChange(lvl.key)}
            className={cn(
              "rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors",
              isActive
                ? "bg-primary text-primary-foreground shadow-xs"
                : "bg-surface-2 text-text-muted hover:bg-surface-3 hover:text-text",
            )}
          >
            {lvl.label}
          </button>
        );
      })}
    </div>
  );
}

