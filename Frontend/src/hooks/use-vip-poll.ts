import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { UserProfile } from "@/types/api";

const POLL_INTERVAL_MS = 2000;
const MAX_ATTEMPTS = 5; // 5 * 2s = 10s, per frontend.md §6's documented window

/** Polls GET /users/me every 2s for up to 10s while the viewer isn't VIP
 * yet — the frontend-side half of payment's eventual-consistency chain
 * (webhook -> outbox -> relay -> account's consumer -> is_vip flips).
 * Stops polling once VIP is confirmed OR the attempt budget runs out;
 * `exhausted` tells the caller to show the "still processing" state. */
export function useVipPoll(enabled: boolean) {
  const attemptsRef = React.useRef(0);
  const [exhausted, setExhausted] = React.useState(false);

  const query = useQuery({
    queryKey: ["profile", "vip-poll"],
    queryFn: async () => {
      const data = await api.get<UserProfile>("/api/users/me");
      attemptsRef.current += 1;
      if (!data.is_vip && attemptsRef.current >= MAX_ATTEMPTS) setExhausted(true);
      return data;
    },
    enabled,
    refetchInterval: (q) => (q.state.data?.is_vip || exhausted ? false : POLL_INTERVAL_MS),
  });

  return { ...query, exhausted };
}
