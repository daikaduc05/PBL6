import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { CategoryTreeResponse } from "@/types/content";

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<CategoryTreeResponse[]>("/api/categories"),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
