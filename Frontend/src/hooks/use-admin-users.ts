"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { UserProfile } from "@/types/api";

interface PaginatedUsers {
  items: UserProfile[];
  total: number;
  page: number;
  size: number;
}

export function useAdminStudents(params?: { q?: string; status?: string }) {
  const queryStr = new URLSearchParams();
  if (params?.q) queryStr.set("q", params.q);
  if (params?.status && params.status !== "all") queryStr.set("status", params.status);

  return useQuery({
    queryKey: ["admin", "students", params],
    queryFn: () => api.get<PaginatedUsers>(`/api/admin/users?${queryStr.toString()}`),
  });
}

export function useAdminEditors() {
  return useQuery({
    queryKey: ["admin", "editors"],
    queryFn: () => api.get<UserProfile[]>("/api/admin/editors"),
  });
}

export function useUpdateUserStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userId,
      status,
      reason,
    }: {
      userId: string;
      status: "ACTIVE" | "LOCKED";
      reason?: string;
    }) => api.patch<UserProfile>(`/api/admin/users/${userId}/status`, { status, reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "students"] });
    },
  });
}

export function useUpdateUserVip() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userId,
      isVip,
      vipExpiredAt,
    }: {
      userId: string;
      isVip: boolean;
      vipExpiredAt?: string | null;
    }) =>
      api.patch<UserProfile>(`/api/admin/users/${userId}/vip`, {
        is_vip: isVip,
        vip_expired_at: vipExpiredAt,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "students"] });
    },
  });
}

export function useCreateEditor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { email: string; full_name: string; password?: string }) =>
      api.post<UserProfile>("/api/admin/editors", body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "editors"] });
    },
  });
}
