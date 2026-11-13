"use client";

import * as React from "react";
import Link from "next/link";
import { Crown, Sparkles, Check, ArrowRight, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface VipGateProps {
  isVip: boolean;
  children: React.ReactNode;
  title?: string;
  description?: string;
  className?: string;
}

export function VipGate({
  isVip,
  children,
  title = "Nội dung dành riêng cho thành viên VIP",
  description = "Bài học này chứa kiến thức nâng cao và tài liệu chuyên sâu dành cho học viên đăng ký gói VIP.",
  className,
}: VipGateProps) {
  if (isVip) {
    return <>{children}</>;
  }

  const vipPerks = [
    "Mở khoá toàn bộ bài học nâng cao & phân tích ngữ pháp chuyên sâu",
    "Trọn bộ bài kiểm tra trắc nghiệm có giải thích đáp án chi tiết",
    "Tải và luyện nghe không giới hạn audio phát âm chuẩn bản xứ",
    "Ưu tiên nhận gợi ý bài học thông minh theo năng lực cá nhân",
  ];

  return (
    <Card
      className={cn(
        "relative overflow-hidden border-2 border-secondary/50 bg-gradient-to-br from-secondary/15 via-surface to-amber-400/10 p-6 sm:p-8 shadow-md",
        className,
      )}
    >
      <div className="flex flex-col items-center text-center space-y-4">
        {/* Badge Icon */}
        <div className="relative">
          <div className="flex size-16 items-center justify-center rounded-full bg-gradient-to-br from-secondary to-amber-400 text-secondary-foreground shadow-lg">
            <Crown className="size-8" aria-hidden />
          </div>
          <div className="absolute -bottom-1 -right-1 flex size-6 items-center justify-center rounded-full bg-surface border-2 border-surface text-secondary-foreground shadow-xs">
            <Lock className="size-3 text-amber-600" />
          </div>
        </div>

        {/* Heading & Subtitle */}
        <div className="max-w-md space-y-1.5">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-secondary/20 px-3 py-1 text-xs font-semibold text-secondary-foreground">
            <Sparkles className="size-3.5" aria-hidden />
            <span>Nội dung VIP</span>
          </div>
          <h3 className="text-h2 text-text font-bold">{title}</h3>
          <p className="text-body-sm text-text-muted">{description}</p>
        </div>

        {/* Perks Checklist */}
        <div className="w-full max-w-md rounded-xl border border-secondary/20 bg-surface/80 p-4 text-left shadow-xs">
          <p className="mb-2.5 text-xs font-bold uppercase tracking-wider text-text-muted">
            Đặc quyền thành viên VIP:
          </p>
          <ul className="space-y-2 text-body-sm text-text">
            {vipPerks.map((perk, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <Check className="size-4 shrink-0 text-amber-500 mt-0.5" aria-hidden />
                <span>{perk}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* CTA Button */}
        <div className="pt-2">
          <Button asChild size="lg" variant="secondary" className="shadow-md font-semibold px-6">
            <Link href="/checkout">
              <Crown className="size-4" aria-hidden />
              Nâng cấp VIP ngay
              <ArrowRight className="size-4 ml-1" aria-hidden />
            </Link>
          </Button>
          <p className="mt-2 text-xs text-text-muted">Kích hoạt tức thì • Học mọi lúc mọi nơi</p>
        </div>
      </div>
    </Card>
  );
}
