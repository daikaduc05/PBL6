"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, FieldError } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { api, ClientApiError } from "@/lib/api-client";

// Matches the backend's ResetPasswordRequest (account/schemas/auth.py):
// new_password 8-72 chars, 72 is bcrypt's hard limit.
const schema = z
  .object({
    new_password: z
      .string()
      .min(8, "Mật khẩu phải có ít nhất 8 ký tự.")
      .max(72, "Mật khẩu tối đa 72 ký tự."),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Mật khẩu xác nhận không khớp.",
    path: ["confirm_password"],
  });
type FormValues = z.infer<typeof schema>;

// useSearchParams() requires a Suspense boundary even on a client page
// (same reason login/page.tsx splits into a wrapper + inner form).
export default function ResetPasswordPage() {
  return (
    <React.Suspense fallback={null}>
      <ResetPasswordForm />
    </React.Suspense>
  );
}

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [formError, setFormError] = React.useState<string | null>(null);
  const [done, setDone] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    if (!token) return;
    setFormError(null);
    try {
      await api.post("/api/auth/reset-password", { token, new_password: values.new_password });
      setDone(true);
    } catch (err) {
      if (err instanceof ClientApiError && err.code === "UNAUTHORIZED") {
        setFormError("Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.");
      } else {
        setFormError("Đã có lỗi xảy ra, vui lòng thử lại.");
      }
    }
  }

  if (!token) {
    return (
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>Liên kết không hợp lệ</CardTitle>
          <CardDescription>
            Thiếu mã đặt lại mật khẩu. Vui lòng mở lại liên kết từ email đã nhận.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-center text-sm text-text-muted">
            <Link href="/forgot-password" className="font-medium text-primary hover:underline">
              Gửi lại yêu cầu đặt lại mật khẩu
            </Link>
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle>Đặt lại mật khẩu</CardTitle>
        <CardDescription>Nhập mật khẩu mới cho tài khoản của bạn.</CardDescription>
      </CardHeader>
      <CardContent>
        {done ? (
          <>
            <p className="rounded-sm border border-success/30 bg-success/10 p-3 text-sm text-success">
              Mật khẩu của bạn đã được đặt lại thành công.
            </p>
            <Button type="button" className="mt-6 w-full" onClick={() => router.push("/login")}>
              Đăng nhập ngay
            </Button>
          </>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div>
              <Label htmlFor="new_password">Mật khẩu mới</Label>
              <Input
                id="new_password"
                type="password"
                autoComplete="new-password"
                error={!!errors.new_password}
                className="mt-1.5"
                {...register("new_password")}
              />
              <FieldError>{errors.new_password?.message}</FieldError>
            </div>

            <div>
              <Label htmlFor="confirm_password">Xác nhận mật khẩu</Label>
              <Input
                id="confirm_password"
                type="password"
                autoComplete="new-password"
                error={!!errors.confirm_password}
                className="mt-1.5"
                {...register("confirm_password")}
              />
              <FieldError>{errors.confirm_password?.message}</FieldError>
            </div>

            {formError && <p className="text-sm text-danger">{formError}</p>}

            <Button type="submit" className="w-full" loading={isSubmitting}>
              Đặt lại mật khẩu
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
