"use client";

import { useRouter } from "next/navigation";
import { Check, Crown, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useCheckout } from "@/hooks/use-checkout";
import { useToast } from "@/hooks/use-toast";
import { errorMessageFor } from "@/lib/error-messages";
import { formatVnd } from "@/lib/utils";
import { ClientApiError } from "@/lib/api-client";
import { PLAN, type CheckoutResponse } from "@/types/api";

const PERKS = [
  "Không giới hạn bài học VIP",
  "Không quảng cáo",
  "Hỗ trợ ưu tiên",
  "Huy hiệu VIP trên hồ sơ",
];

export default function CheckoutPage() {
  const router = useRouter();
  const toast = useToast();
  const checkout = useCheckout();

  async function handleCheckout() {
    try {
      const result: CheckoutResponse = await checkout.mutateAsync(PLAN.code);
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
    <div className="mx-auto max-w-md py-4">
      <div className="mb-8 text-center">
        <h1 className="text-h1 text-text">Nâng cấp VIP</h1>
        <p className="mt-2 text-body-sm text-text-muted">
          Mở khoá toàn bộ trải nghiệm học tiếng Anh.
        </p>
      </div>

      <Card className="overflow-hidden shadow-lg">
        <div className="bg-gradient-to-br from-secondary/15 via-surface to-surface">
          <CardHeader className="flex flex-col items-center pb-6 text-center">
            <div className="relative mb-2">
              <div
                aria-hidden
                className="absolute inset-0 -z-10 rounded-full bg-secondary/30 blur-2xl"
              />
              <span className="flex size-16 items-center justify-center rounded-full bg-gradient-to-br from-secondary to-amber-400 shadow-md">
                <Crown className="size-8 text-secondary-foreground" aria-hidden />
              </span>
            </div>
            <p className="text-caption uppercase tracking-wide text-text-muted">Gói VIP</p>
            <p className="text-display text-text">{formatVnd(PLAN.amount)}</p>
            <p className="text-body-sm text-text-muted">
              cho {PLAN.duration_days} ngày sử dụng
            </p>
          </CardHeader>
        </div>

        <CardContent className="space-y-6">
          <ul className="space-y-3">
            {PERKS.map((perk) => (
              <li key={perk} className="flex items-center gap-3 text-body-sm text-text">
                <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-success/15">
                  <Check className="size-3.5 text-success" aria-hidden />
                </span>
                {perk}
              </li>
            ))}
          </ul>

          <Button size="lg" className="w-full" loading={checkout.isPending} onClick={handleCheckout}>
            <Crown className="size-4" aria-hidden />
            Thanh toán qua chuyển khoản
          </Button>

          <p className="flex items-center justify-center gap-1.5 text-caption text-text-muted">
            <ShieldCheck className="size-3.5" aria-hidden />
            Xác nhận tự động qua chuyển khoản ngân hàng (SePay)
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
