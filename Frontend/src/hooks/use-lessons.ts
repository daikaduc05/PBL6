import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { LessonListResponse, LessonQueryParams } from "@/types/content";

export function useLessons(params: LessonQueryParams = {}) {
  const query = new URLSearchParams();
  if (params.category_id) query.set("category_id", params.category_id);
  if (params.level && params.level !== "all") query.set("level", params.level);
  if (params.q) query.set("q", params.q);
  if (params.page) query.set("page", params.page.toString());
  if (params.size) query.set("size", params.size.toString());

  const queryString = query.toString();
  const url = queryString ? `/api/lessons?${queryString}` : "/api/lessons";

  return useQuery({
    queryKey: ["lessons", params],
    queryFn: () => api.get<LessonListResponse>(url),
    staleTime: 60 * 1000,
  });
}
