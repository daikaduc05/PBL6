"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Lesson } from "@/types/content";

interface FavoritesListResponse {
  items: (Lesson & { favorited_at?: string })[];
  total: number;
}

interface FavoriteStatusResponse {
  lesson_id: string;
  is_favorite: boolean;
}

export function useFavorites() {
  return useQuery({
    queryKey: ["favorites"],
    queryFn: () => api.get<FavoritesListResponse>("/api/learning/favorites"),
    staleTime: 30 * 1000,
  });
}

export function useFavoriteStatus(lessonId: string) {
  return useQuery({
    queryKey: ["favorite-status", lessonId],
    queryFn: () => api.get<FavoriteStatusResponse>(`/api/learning/favorites/${lessonId}`),
    staleTime: 60 * 1000,
  });
}

export function useToggleFavorite(lessonId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (isFavoriteNow: boolean) => {
      if (isFavoriteNow) {
        await api.delete(`/api/learning/favorites/${lessonId}`);
        return false;
      } else {
        await api.post(`/api/learning/favorites/${lessonId}`);
        return true;
      }
    },
    onSuccess: (newStatus) => {
      queryClient.setQueryData(["favorite-status", lessonId], {
        lesson_id: lessonId,
        is_favorite: newStatus,
      });
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
    },
  });
}
