"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useVipPoll } from "@/hooks/use-vip-poll";
import { useToast } from "@/hooks/use-toast";
import { formatVnd } from "@/lib/utils";
import type { CheckoutResponse } from "@/types/api";

// frontend.md §6, "The VIP eventual-consistency case (T33)": after
// checkout, poll GET /users/me for up to 10s. While not VIP yet, show
// "Đang xử lý thanh toán…"; if the window elapses, say it'll activate
// shortly with a manual refresh — never show a failure, since the
// transfer (once SePay confirms it) did succeed.
export default function CheckoutResultPage() {
  return (
    <React.Suspense fallback={null}>
      <CheckoutResult />
    </React.Suspense>
  );
}

function CheckoutResult() {
  const searchParams = useSearchParams();
  const txId = searchParams.get("tx");
  const toast = useToast();

  const [checkoutInfo, setCheckoutInfo] = React.useState<CheckoutResponse | null>(null);
  React.useEffect(() => {
    if (!txId) return;
    const raw = sessionStorage.getItem(`pbl6_checkout_${txId}`);
    if (raw) setCheckoutInfo(JSON.parse(raw) as CheckoutResponse);
  }, [txId]);

  const { data: profile, exhausted } = useVipPoll(!!txId);

  function copyContent() {
    if (!checkoutInfo) return;
    navigator.clipboard.writeText(checkoutInfo.transfer_content);
    toast.info("Đã sao chép nội dung chuyển khoản.");
  }

  if (!txId || !checkoutInfo) {
    return (
      <Card className="mx-auto max-w-md">
        <CardContent className="py-8 text-center text-text-muted">
          Không tìm thấy thông tin giao dịch.{" "}
          <Link href="/checkout" className="text-primary hover:underline">
            Quay lại chọn gói
          </Link>
          .
        </CardContent>
      </Card>
    );
  }

  if (profile?.is_vip) {
    return (
      <Card className="mx-auto max-w-md">
        <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
          <CheckCircle2 className="size-12 text-success" aria-hidden />
          <h1 className="text-xl font-bold text-text">Thanh toán thành công!</h1>
          <p className="text-text-muted">Tài khoản của bạn đã được nâng cấp lên VIP.</p>
          <Button asChild className="mt-2">
            <Link href="/profile">Về trang cá nhân</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader className="text-center">
        <CardTitle>Quét mã để thanh toán</CardTitle>
        <CardDescription>
          Dùng app ngân hàng quét mã QR bên dưới — hệ thống sẽ tự động xác nhận.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-4">
        <Image
          src={checkoutInfo.qr_code_url}
          alt="Mã QR thanh toán VietQR"
          width={240}
          height={240}
          className="rounded-md border border-border"
          unoptimized
        />

        <div className="w-full space-y-2 rounded-md bg-surface-2 p-4 text-sm">
          <div className="flex justify-between">
            <span className="text-text-muted">Số tiền</span>
            <span className="font-semibold text-text">{formatVnd(checkoutInfo.amount)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Ngân hàng</span>
            <span className="font-medium text-text">{checkoutInfo.bank_code}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Số tài khoản</span>
            <span className="font-medium text-text">{checkoutInfo.bank_account_number}</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="shrink-0 text-text-muted">Nội dung</span>
            <span className="flex items-center gap-1 truncate font-mono font-medium text-text">
              {checkoutInfo.transfer_content}
              <button onClick={copyContent} aria-label="Sao chép nội dung chuyển khoản">
                <Copy className="size-3.5 text-text-muted hover:text-text" />
              </button>
            </span>
          </div>
        </div>

        {exhausted ? (
          <div className="w-full rounded-md border border-warning/30 bg-warning/10 p-3 text-center text-sm text-warning">
            Giao dịch có thể mất thêm chút thời gian để xác nhận. VIP sẽ tự động kích hoạt ngay khi
            hệ thống nhận được thanh toán.
            <Button variant="link" className="mt-1 block" onClick={() => window.location.reload()}>
              Kiểm tra lại
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Spinner className="size-4" />
            Đang chờ xác nhận thanh toán…
          </div>
        )}
      </CardContent>
    </Card>
  );
}
