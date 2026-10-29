import * as React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

// design-system.md §8: variants primary/secondary/outline/ghost/destructive/
// link; sizes sm(32px)/md(40px)/lg(48px); disabled = 50% opacity, no
// pointer events; loading = spinner replaces label, width unchanged.
const VARIANT_CLASSES: Record<string, string> = {
  primary: "bg-primary text-primary-foreground hover:bg-primary-hover shadow-sm",
  secondary: "bg-secondary text-secondary-foreground hover:brightness-95 shadow-sm",
  outline: "border border-border bg-background hover:bg-surface text-text",
  ghost: "hover:bg-surface text-text",
  destructive: "bg-danger text-danger-foreground hover:brightness-90 shadow-sm",
  link: "text-primary underline-offset-4 hover:underline h-auto p-0",
};

const SIZE_CLASSES: Record<string, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-base",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof VARIANT_CLASSES;
  size?: keyof typeof SIZE_CLASSES;
  loading?: boolean;
  /** Renders the single child element (e.g. next/link's <Link>) with the
   * button's classes instead of a <button> — a minimal stand-in for Radix's
   * Slot, just enough for "a link that looks like a button." */
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      loading = false,
      disabled,
      asChild = false,
      children,
      ...props
    },
    ref,
  ) => {
    const classes = cn(
      "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      "disabled:pointer-events-none disabled:opacity-50",
      VARIANT_CLASSES[variant],
      variant !== "link" && SIZE_CLASSES[size],
      className,
    );

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children as React.ReactElement<{ className?: string }>, {
        className: cn(
          classes,
          (children as React.ReactElement<{ className?: string }>).props.className,
        ),
      });
    }

    return (
      <button ref={ref} disabled={disabled || loading} className={classes} {...props}>
        {loading && <Loader2 className="size-4 animate-spin" aria-hidden />}
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";
