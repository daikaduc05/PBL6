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

const schema = z.object({ email: z.string().email("Email không hợp lệ.") });
type FormValues = z.infer<typeof schema>;

// Backend has no password-reset endpoint yet (account/api/v1/auth.py only
// has register/login/refresh/logout) — there's nothing for this form to
// call. Shipping the screen anyway (frontend.md lists it under T32) but
// being honest about the gap instead of faking success, same policy this
// project has followed for every other backend gap (see T29's commit for
// the precedent).
export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = React.useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quên mật khẩu</CardTitle>
        <CardDescription>Nhập email để nhận hướng dẫn đặt lại mật khẩu.</CardDescription>
      </CardHeader>
      <CardContent>
        {submitted ? (
          <p className="rounded-sm border border-warning/30 bg-warning/10 p-3 text-sm text-warning">
            Tính năng đặt lại mật khẩu đang được phát triển. Vui lòng liên hệ quản trị viên để được
            hỗ trợ trong lúc này.
          </p>
        ) : (
          <form onSubmit={handleSubmit(() => setSubmitted(true))} className="space-y-4" noValidate>
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
            <Button type="submit" className="w-full">
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
