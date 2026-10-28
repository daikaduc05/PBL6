"use client";

import * as React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Crown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, FieldError } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { VipBadge } from "@/components/ui/badge";
import { useProfile, useUpdateProfile, useChangePassword } from "@/hooks/use-profile";
import { useToast } from "@/hooks/use-toast";
import { errorMessageFor } from "@/lib/error-messages";
import { formatDate } from "@/lib/utils";
import { ClientApiError } from "@/lib/api-client";

const profileSchema = z.object({ full_name: z.string().min(1, "Vui lòng nhập họ tên.").max(200) });
type ProfileValues = z.infer<typeof profileSchema>;

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Vui lòng nhập mật khẩu hiện tại."),
    new_password: z.string().min(8, "Mật khẩu mới phải có ít nhất 8 ký tự.").max(72),
    confirm_password: z.string(),
  })
  .refine((v) => v.new_password === v.confirm_password, {
    message: "Mật khẩu xác nhận không khớp.",
    path: ["confirm_password"],
  });
type PasswordValues = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const { data: profile, isLoading } = useProfile();
  const toast = useToast();

  const updateProfile = useUpdateProfile();
  const profileForm = useForm<ProfileValues>({ resolver: zodResolver(profileSchema) });

  React.useEffect(() => {
    if (profile) profileForm.reset({ full_name: profile.full_name });
  }, [profile, profileForm]);

  async function onSaveProfile(values: ProfileValues) {
    try {
      await updateProfile.mutateAsync(values.full_name);
      toast.success("Đã cập nhật thông tin cá nhân.");
    } catch (err) {
      toast.error(err instanceof ClientApiError ? errorMessageFor(err.code) : "Đã có lỗi xảy ra.");
    }
  }

  const changePassword = useChangePassword();
  const passwordForm = useForm<PasswordValues>({ resolver: zodResolver(passwordSchema) });

  async function onChangePassword(values: PasswordValues) {
    try {
      await changePassword.mutateAsync(values);
      toast.success("Đã đổi mật khẩu.");
      passwordForm.reset({ current_password: "", new_password: "", confirm_password: "" });
    } catch (err) {
      toast.error(err instanceof ClientApiError ? errorMessageFor(err.code) : "Đã có lỗi xảy ra.");
    }
  }

  if (isLoading || !profile) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-text">Thông tin cá nhân</h1>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Trạng thái VIP</CardTitle>
            <CardDescription>
              {profile.is_vip && profile.vip_expired_at
                ? `Hết hạn ngày ${formatDate(profile.vip_expired_at)}`
                : "Bạn chưa có gói VIP."}
            </CardDescription>
          </div>
          {profile.is_vip ? (
            <VipBadge />
          ) : (
            <Button asChild size="sm" variant="secondary">
              <Link href="/checkout">
                <Crown className="size-4" aria-hidden />
                Nâng cấp VIP
              </Link>
            </Button>
          )}
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Thông tin cơ bản</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={profileForm.handleSubmit(onSaveProfile)} className="space-y-4" noValidate>
            <div>
              <Label>Email</Label>
              <Input value={profile.email} disabled className="mt-1.5" />
            </div>
            <div>
              <Label htmlFor="full_name">Họ tên</Label>
              <Input
                id="full_name"
                error={!!profileForm.formState.errors.full_name}
                className="mt-1.5"
                {...profileForm.register("full_name")}
              />
              <FieldError>{profileForm.formState.errors.full_name?.message}</FieldError>
            </div>
            <Button type="submit" loading={profileForm.formState.isSubmitting}>
              Lưu thay đổi
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Đổi mật khẩu</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={passwordForm.handleSubmit(onChangePassword)}
            className="space-y-4"
            noValidate
          >
            <div>
              <Label htmlFor="current_password">Mật khẩu hiện tại</Label>
              <Input
                id="current_password"
                type="password"
                autoComplete="current-password"
                error={!!passwordForm.formState.errors.current_password}
                className="mt-1.5"
                {...passwordForm.register("current_password")}
              />
              <FieldError>{passwordForm.formState.errors.current_password?.message}</FieldError>
            </div>
            <div>
              <Label htmlFor="new_password">Mật khẩu mới</Label>
              <Input
                id="new_password"
                type="password"
                autoComplete="new-password"
                error={!!passwordForm.formState.errors.new_password}
                className="mt-1.5"
                {...passwordForm.register("new_password")}
              />
              <FieldError>{passwordForm.formState.errors.new_password?.message}</FieldError>
            </div>
            <div>
              <Label htmlFor="confirm_password">Xác nhận mật khẩu mới</Label>
              <Input
                id="confirm_password"
                type="password"
                autoComplete="new-password"
                error={!!passwordForm.formState.errors.confirm_password}
                className="mt-1.5"
                {...passwordForm.register("confirm_password")}
              />
              <FieldError>{passwordForm.formState.errors.confirm_password?.message}</FieldError>
            </div>
            <Button type="submit" variant="outline" loading={passwordForm.formState.isSubmitting}>
              Đổi mật khẩu
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
