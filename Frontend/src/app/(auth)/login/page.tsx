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
import { errorMessageFor } from "@/lib/error-messages";

const schema = z.object({
  email: z.string().email("Email không hợp lệ."),
  password: z.string().min(1, "Vui lòng nhập mật khẩu."),
});
type FormValues = z.infer<typeof schema>;

// useSearchParams() requires a Suspense boundary even on a client page
// (Next.js opts the subtree into it during prerendering) — the default
// export below just supplies that; LoginForm holds the real page.
export default function LoginPage() {
  return (
    <React.Suspense fallback={null}>
      <LoginForm />
    </React.Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [formError, setFormError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    try {
      await api.post("/api/auth/login", values);
      const next = searchParams.get("next") || "/profile";
      router.push(next);
      router.refresh();
    } catch (err) {
      setFormError(err instanceof ClientApiError ? errorMessageFor(err.code) : "Đã có lỗi xảy ra.");
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Đăng nhập</CardTitle>
        <CardDescription>Chào mừng bạn quay lại PBL6.</CardDescription>
      </CardHeader>
      <CardContent>
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

          <div>
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Mật khẩu</Label>
              <Link href="/forgot-password" className="text-sm text-primary hover:underline">
                Quên mật khẩu?
              </Link>
            </div>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              error={!!errors.password}
              className="mt-1.5"
              {...register("password")}
            />
            <FieldError>{errors.password?.message}</FieldError>
          </div>

          {formError && <p className="text-sm text-danger">{formError}</p>}

          <Button type="submit" className="w-full" loading={isSubmitting}>
            Đăng nhập
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-text-muted">
          Chưa có tài khoản?{" "}
          <Link href="/register" className="font-medium text-primary hover:underline">
            Đăng ký
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
