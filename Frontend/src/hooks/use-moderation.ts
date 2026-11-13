"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Lesson } from "@/types/content";

interface ModerationListResponse {
  items: Lesson[];
  total: number;
}

export function usePendingLessons() {
  return useQuery({
    queryKey: ["admin", "moderation"],
    queryFn: () => api.get<ModerationListResponse>("/api/admin/moderation"),
  });
}

export function useApproveLesson() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (lessonId: string) => api.post<Lesson>(`/api/admin/lessons/${lessonId}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "moderation"] });
      queryClient.invalidateQueries({ queryKey: ["lessons"] });
    },
  });
}

export function useRejectLesson() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ lessonId, reason }: { lessonId: string; reason?: string }) =>
      api.post<Lesson>(`/api/admin/lessons/${lessonId}/reject`, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "moderation"] });
      queryClient.invalidateQueries({ queryKey: ["lessons"] });
    },
  });
}
