"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, FieldError } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { api, ClientApiError } from "@/lib/api-client";
import { errorMessageFor } from "@/lib/error-messages";

// Matches the backend's own constraints exactly (account/schemas/auth.py
// RegisterRequest): password 8-72 chars, 72 is bcrypt's hard limit.
const schema = z.object({
  full_name: z.string().min(1, "Vui lòng nhập họ tên.").max(200),
  email: z.string().email("Email không hợp lệ."),
  password: z
    .string()
    .min(8, "Mật khẩu phải có ít nhất 8 ký tự.")
    .max(72, "Mật khẩu tối đa 72 ký tự."),
});
type FormValues = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const [formError, setFormError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    try {
      await api.post("/api/auth/register", values);
      router.push("/profile");
      router.refresh();
    } catch (err) {
      setFormError(err instanceof ClientApiError ? errorMessageFor(err.code) : "Đã có lỗi xảy ra.");
    }
  }

  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle>Tạo tài khoản</CardTitle>
        <CardDescription>Bắt đầu hành trình tự học tiếng Anh của bạn.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div>
            <Label htmlFor="full_name">Họ tên</Label>
            <Input
              id="full_name"
              autoComplete="name"
              error={!!errors.full_name}
              className="mt-1.5"
              {...register("full_name")}
            />
            <FieldError>{errors.full_name?.message}</FieldError>
          </div>

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
            <Label htmlFor="password">Mật khẩu</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              error={!!errors.password}
              className="mt-1.5"
              {...register("password")}
            />
            <FieldError>{errors.password?.message}</FieldError>
          </div>

          {formError && <p className="text-sm text-danger">{formError}</p>}

          <Button type="submit" className="w-full" loading={isSubmitting}>
            Đăng ký
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-text-muted">
          Đã có tài khoản?{" "}
          <Link href="/login" className="font-medium text-primary hover:underline">
            Đăng nhập
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
