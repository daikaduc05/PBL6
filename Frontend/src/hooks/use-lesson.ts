import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Lesson, MediaAsset } from "@/types/content";

export function useLesson(id: string) {
  return useQuery({
    queryKey: ["lesson", id],
    queryFn: () => api.get<Lesson>(`/api/lessons/${id}`),
    enabled: Boolean(id),
    staleTime: 60 * 1000,
  });
}

export function useLessonMedia(lessonId: string) {
  return useQuery({
    queryKey: ["lesson-media", lessonId],
    queryFn: () => api.get<MediaAsset[]>(`/api/media/lessons/${lessonId}`),
    enabled: Boolean(lessonId),
    staleTime: 5 * 60 * 1000,
  });
}
