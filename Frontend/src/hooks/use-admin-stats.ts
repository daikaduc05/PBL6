"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface AdminStatsResponse {
  lessons: {
    total: number;
    published: number;
    pending: number;
    draft: number;
    rejected: number;
  };
  categories: {
    total: number;
  };
  students: {
    total: number;
    vip: number;
    locked: number;
  };
}

export function useAdminStats() {
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: () => api.get<AdminStatsResponse>("/api/admin/stats"),
    staleTime: 30 * 1000,
  });
}
