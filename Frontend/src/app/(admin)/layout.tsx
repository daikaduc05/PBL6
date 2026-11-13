import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { accountApi } from "@/lib/backend-client";
import { Header } from "@/components/layout/header";
import type { UserProfile } from "@/types/api";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const user = await getSession();
  if (!user) redirect("/login");

  const roles = user.roles.map((r) => r.toUpperCase());
  if (!roles.includes("ADMIN") && !roles.includes("EDITOR")) {
    redirect("/categories");
  }

  const profile = await accountApi.get<UserProfile>("/users/me", { user });

  return (
    <div className="min-h-svh bg-background">
      <Header user={{ fullName: profile.full_name, isVip: profile.is_vip, role: profile.role }} />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">{children}</main>
    </div>
  );
}
