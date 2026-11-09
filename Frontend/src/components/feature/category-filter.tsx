import { cn } from "@/lib/utils";
import type { CategoryTreeResponse } from "@/types/content";

export interface CategoryFilterProps {
  categories: CategoryTreeResponse[];
  selectedCategoryId: string | null;
  onSelectCategory: (id: string | null) => void;
  className?: string;
}

export function CategoryFilter({
  categories,
  selectedCategoryId,
  onSelectCategory,
  className,
}: CategoryFilterProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <button
        type="button"
        onClick={() => onSelectCategory(null)}
        className={cn(
          "rounded-lg px-3 py-1.5 text-body-sm font-medium transition-colors",
          selectedCategoryId === null
            ? "bg-primary/10 text-primary font-semibold border border-primary/20"
            : "text-text-muted hover:bg-surface-2 hover:text-text",
        )}
      >
        Tất cả chủ đề
      </button>

      {categories.map((cat) => {
        const isSelected = selectedCategoryId === cat.id;
        return (
          <button
            key={cat.id}
            type="button"
            onClick={() => onSelectCategory(cat.id)}
            className={cn(
              "rounded-lg px-3 py-1.5 text-body-sm font-medium transition-colors",
              isSelected
                ? "bg-primary/10 text-primary font-semibold border border-primary/20"
                : "text-text-muted hover:bg-surface-2 hover:text-text",
            )}
          >
            {cat.name}
          </button>
        );
      })}
    </div>
  );
}

