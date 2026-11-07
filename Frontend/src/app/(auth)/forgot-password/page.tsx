"use client";

import * as React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, FieldError } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { api } from "@/lib/api-client";

const schema = z.object({ email: z.string().email("Email không hợp lệ.") });
type FormValues = z.infer<typeof schema>;

// POST /api/auth/forgot-password always returns 204 (the backend never
// reveals whether the email is registered — same response either way), so
// this form always shows the same success message regardless of outcome.
export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    try {
      await api.post("/api/auth/forgot-password", values);
      setSubmitted(true);
    } catch {
      setFormError("Đã có lỗi xảy ra, vui lòng thử lại.");
    }
  }

  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle>Quên mật khẩu</CardTitle>
        <CardDescription>Nhập email để nhận hướng dẫn đặt lại mật khẩu.</CardDescription>
      </CardHeader>
      <CardContent>
        {submitted ? (
          <p className="rounded-sm border border-success/30 bg-success/10 p-3 text-sm text-success">
            Nếu email này đã được đăng ký, chúng tôi đã gửi một liên kết đặt lại mật khẩu đến đó.
            Vui lòng kiểm tra hộp thư (và thư mục spam) — liên kết hết hạn sau 1 giờ.
          </p>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                error={!!errors.email}
                className="mt-1.5"
                {...register("email")}
              />
              <FieldError>{errors.email?.message}</FieldError>
            </div>

            {formError && <p className="text-sm text-danger">{formError}</p>}

            <Button type="submit" className="w-full" loading={isSubmitting}>
              Gửi yêu cầu
            </Button>
          </form>
        )}

        <p className="mt-6 text-center text-sm text-text-muted">
          <Link href="/login" className="font-medium text-primary hover:underline">
            Quay lại đăng nhập
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
