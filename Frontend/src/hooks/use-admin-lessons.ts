"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Lesson, LessonListResponse, LessonLevel, LessonAccess } from "@/types/content";

export function useAdminLessons(params?: { q?: string; level?: string; category_id?: string }) {
  const queryStr = new URLSearchParams();
  if (params?.q) queryStr.set("q", params.q);
  if (params?.level) queryStr.set("level", params.level);
  if (params?.category_id) queryStr.set("category_id", params.category_id);

  return useQuery({
    queryKey: ["admin", "lessons", params],
    queryFn: () => api.get<LessonListResponse>(`/api/admin/lessons?${queryStr.toString()}`),
  });
}

export function useCreateLesson() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      category_id: string;
      title: string;
      body: string;
      level: LessonLevel;
      access: LessonAccess;
    }) => api.post<Lesson>("/api/admin/lessons", body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "lessons"] });
      queryClient.invalidateQueries({ queryKey: ["lessons"] });
    },
  });
}

export function useUpdateLesson() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      ...body
    }: {
      id: string;
      category_id?: string;
      title?: string;
      body?: string;
      level?: LessonLevel;
      access?: LessonAccess;
    }) => api.put<Lesson>(`/api/admin/lessons/${id}`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "lessons"] });
      queryClient.invalidateQueries({ queryKey: ["lessons"] });
    },
  });
}

export function useDeleteLesson() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/admin/lessons/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "lessons"] });
      queryClient.invalidateQueries({ queryKey: ["lessons"] });
    },
  });
}

export function useSubmitLesson() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post<Lesson>(`/api/admin/lessons/${id}/submit`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "lessons"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "moderation"] });
      queryClient.invalidateQueries({ queryKey: ["lessons"] });
    },
  });
}
