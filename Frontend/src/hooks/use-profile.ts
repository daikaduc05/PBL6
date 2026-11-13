import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { UserProfile } from "@/types/api";

export function useProfile() {
  return useQuery({
    queryKey: ["profile"],
    queryFn: () => api.get<UserProfile>("/api/users/me"),
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (full_name: string) => api.patch<UserProfile>("/api/users/me", { full_name }),
    onSuccess: (profile) => queryClient.setQueryData(["profile"], profile),
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (body: { current_password: string; new_password: string }) =>
      api.post<void>("/api/users/me/change-password", body),
  });
}
