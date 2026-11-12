import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  NotificationPage,
  NotificationSettings,
  UpdateNotificationSettings,
} from "@/types/api";

export const PAGE_SIZE = 20;

/** Every mutation below invalidates this prefix, so the list and the bell's
 * unread count are refetched together and can never disagree. */
const LIST_KEY = ["notifications"] as const;

interface PageQuery {
  page: number;
  unreadOnly: boolean;
}

function fetchPage({ page, unreadOnly }: PageQuery) {
  const params = new URLSearchParams({
    page: String(page),
    size: String(PAGE_SIZE),
    unread_only: String(unreadOnly),
  });
  return api.get<NotificationPage>(`/api/notifications?${params}`);
}

export function useNotifications({ page, unreadOnly }: PageQuery) {
  return useQuery({
    queryKey: [...LIST_KEY, { page, unreadOnly }],
    queryFn: () => fetchPage({ page, unreadOnly }),
    // Keeps the previous page on screen while the next one loads instead of
    // flashing an empty list under the pager.
    placeholderData: (previous) => previous,
  });
}

/** The query the bell reads, and the one the notification page's first page
 * already fetches — same key, so opening that page costs no extra request
 * and the bell updates from the list's own response. */
const UNREAD_PROBE = { page: 1, unreadOnly: false } as const;

/** Just the unread figure, for the header bell.
 *
 * Refetches on window focus (react-query's default), which is enough for a
 * number that changes when a cron fires or a payment lands — polling would
 * cost a request a minute per open tab to show the same digit. */
export function useUnreadCount() {
  return useQuery({
    queryKey: [...LIST_KEY, UNREAD_PROBE],
    queryFn: () => fetchPage(UNREAD_PROBE),
    select: (data) => data.unread_count,
  });
}

export function useMarkRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.patch<void>(`/api/notifications/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: LIST_KEY }),
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ updated: number }>("/api/notifications/read-all"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: LIST_KEY }),
  });
}

export function useDeleteNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.del<void>(`/api/notifications/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: LIST_KEY }),
  });
}

export function useNotificationSettings() {
  return useQuery({
    queryKey: ["notification-settings"],
    queryFn: () => api.get<NotificationSettings>("/api/notifications/settings"),
  });
}

export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateNotificationSettings) =>
      api.put<NotificationSettings>("/api/notifications/settings", body),
    onSuccess: (settings) => queryClient.setQueryData(["notification-settings"], settings),
  });
}
