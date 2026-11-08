import { create } from "zustand";

export type ToastVariant = "success" | "danger" | "warning" | "info";

export interface Toast {
  id: string;
  title: string;
  variant: ToastVariant;
}

interface ToastStore {
  toasts: Toast[];
  push: (title: string, variant?: ToastVariant) => void;
  dismiss: (id: string) => void;
}

// design-system.md §8: "Toast — 4 variants = semantic tokens. Auto-dismiss
// 4s. Bottom-right on web."
const AUTO_DISMISS_MS = 4000;

export const useToastStore = create<ToastStore>((set, get) => ({
  toasts: [],
  push: (title, variant = "info") => {
    const id = crypto.randomUUID();
    set((s) => ({ toasts: [...s.toasts, { id, title, variant }] }));
    setTimeout(() => get().dismiss(id), AUTO_DISMISS_MS);
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export function useToast() {
  const push = useToastStore((s) => s.push);
  return {
    success: (title: string) => push(title, "success"),
    error: (title: string) => push(title, "danger"),
    info: (title: string) => push(title, "info"),
  };
}
