"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Check, Crown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCheckout } from "@/hooks/use-checkout";
import { useToast } from "@/hooks/use-toast";
import { errorMessageFor } from "@/lib/error-messages";
import { formatVnd, cn } from "@/lib/utils";
import { ClientApiError } from "@/lib/api-client";
import { PLANS, type PlanCode } from "@/types/api";
import type { CheckoutResponse } from "@/types/api";

const PLAN_PERKS = ["Không giới hạn bài học VIP", "Không quảng cáo", "Hỗ trợ ưu tiên"];

export default function CheckoutPage() {
  const router = useRouter();
  const toast = useToast();
  const checkout = useCheckout();
  const [selected, setSelected] = React.useState<PlanCode>("VIP_1_MONTH");

  async function handleCheckout() {
    try {
      const result: CheckoutResponse = await checkout.mutateAsync(selected);
      // No GET /payments/{id} exists on the backend (ER diagram dropped
      // it) — the result page can't re-fetch, so it's handed the QR
      // payload directly via sessionStorage and reads it back.
      sessionStorage.setItem(`pbl6_checkout_${result.transaction_id}`, JSON.stringify(result));
      router.push(`/checkout/result?tx=${result.transaction_id}`);
    } catch (err) {
      toast.error(err instanceof ClientApiError ? errorMessageFor(err.code) : "Đã có lỗi xảy ra.");
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-text">Nâng cấp VIP</h1>
        <p className="mt-2 text-text-muted">Chọn gói phù hợp với bạn.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {PLANS.map((plan) => {
          const isSelected = selected === plan.code;
          return (
            <Card
              key={plan.code}
              className={cn(
                "cursor-pointer transition-all",
                isSelected && "border-primary ring-2 ring-primary ring-offset-2",
              )}
              onClick={() => setSelected(plan.code)}
            >
              <CardHeader className="text-center">
                <Crown className="mx-auto size-8 text-secondary" aria-hidden />
                <CardTitle className="mt-2">{plan.name}</CardTitle>
                <p className="text-2xl font-bold text-text">{formatVnd(plan.amount)}</p>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-text-muted">
                  {PLAN_PERKS.map((perk) => (
                    <li key={perk} className="flex items-center gap-2">
                      <Check className="size-4 text-success" aria-hidden />
                      {perk}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="mt-8 flex justify-center">
        <Button size="lg" loading={checkout.isPending} onClick={handleCheckout}>
          Thanh toán qua chuyển khoản
        </Button>
      </div>
    </div>
  );
}
