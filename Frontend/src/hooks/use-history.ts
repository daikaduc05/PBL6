import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { HistoryItem } from "@/types/content";

export function useHistory() {
  return useQuery({
    queryKey: ["history"],
    queryFn: () => api.get<HistoryItem[]>("/api/learning/me/attempts"),
    staleTime: 30 * 1000,
  });
}
