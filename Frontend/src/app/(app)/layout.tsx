import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { accountApi } from "@/lib/backend-client";
import { Header } from "@/components/layout/header";
import type { UserProfile } from "@/types/api";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  // middleware.ts already redirects unauthenticated requests before this
  // ever renders — this check stays as defense in depth per frontend.md
  // §5 ("Server Components read the session with lib/session.ts").
  const user = await getSession();
  if (!user) redirect("/login");

  const profile = await accountApi.get<UserProfile>("/users/me", { user });

  return (
    <div className="min-h-svh bg-background">
      <Header fullName={profile.full_name} isVip={profile.is_vip} />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">{children}</main>
    </div>
  );
}
