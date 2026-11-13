import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { CheckoutResponse, PlanCode } from "@/types/api";

export function useCheckout() {
  return useMutation({
    mutationFn: (plan_code: PlanCode) =>
      api.post<CheckoutResponse>("/api/payments/checkout", { plan_code }),
  });
}
