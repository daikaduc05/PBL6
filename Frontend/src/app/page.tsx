import Link from "next/link";
import { BookOpen, Crown, Sparkles, UserRound } from "lucide-react";
import { getSession, type SessionUser } from "@/lib/session";
import { accountApi } from "@/lib/backend-client";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { VipBadge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { UserProfile } from "@/types/api";

// Public home page: a visitor with no account lands here and can look around
// before deciding to sign up, so this route is deliberately NOT in the (app)
// group (whose layout redirects to /login). It renders its own Header because
// of that, and the Header shows login/register instead of the account area
// when there is no session.
/** The profile is a nice-to-have here (a name and a VIP badge), not what the
 * page is for. Unlike /profile this route has no middleware in front of it
 * and must render for anyone, so a failing account service degrades the
 * greeting instead of taking the front door down with it. */
async function loadProfile(session: SessionUser | null): Promise<UserProfile | null> {
  if (!session) return null;
  try {
    return await accountApi.get<UserProfile>("/users/me", { user: session });
  } catch (err) {
    console.error("home: could not load profile, rendering signed-out view", err);
    return null;
  }
}

export default async function HomePage() {
  const session = await getSession();
  const profile = await loadProfile(session);

  // Signed-out visitors get the same layout with every action pointing at
  // /login — one page to maintain instead of two that drift apart.
  const learnHref = profile ? "/lessons" : "/login";
  const vipHref = profile ? "/checkout" : "/login";

  return (
    <div className="min-h-svh bg-background">
      <Header user={profile ? { fullName: profile.full_name, isVip: profile.is_vip } : undefined} />

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6">
        <section className="space-y-2">
          {profile ? (
            <>
              <div className="flex items-center gap-3">
                <h1 className="text-h1 text-text">Chào {profile.full_name}!</h1>
                {profile.is_vip && <VipBadge />}
              </div>
              <p className="text-body text-text-muted">
                Hôm nay học gì tiếp? Giữ nhịp mỗi ngày một chút là cách chắc nhất để tiến bộ.
              </p>
            </>
          ) : (
            <>
              <h1 className="text-h1 text-text">Học tiếng Anh mỗi ngày một chút</h1>
              <p className="text-body text-text-muted">
                Bài học từ vựng và ngữ pháp theo chủ đề, kèm trắc nghiệm và nhắc học hằng ngày. Tạo
                tài khoản miễn phí để bắt đầu.
              </p>
              <div className="flex gap-3 pt-2">
                <Button asChild>
                  <Link href="/register">Bắt đầu miễn phí</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="/login">Tôi đã có tài khoản</Link>
                </Button>
              </div>
            </>
          )}
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <BookOpen className="size-6 text-primary" aria-hidden />
              <CardTitle>Học bài</CardTitle>
              <CardDescription>
                Kho bài học từ vựng và ngữ pháp theo chủ đề, kèm trắc nghiệm.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* /lessons does not exist yet — pointed at it anyway so this
                  page needs no edit once the content UI lands. */}
              <Button asChild variant="outline" size="sm">
                <Link href={learnHref}>Vào kho bài học</Link>
              </Button>
            </CardContent>
          </Card>

          {!profile?.is_vip && (
            <Card>
              <CardHeader>
                <Crown className="size-6 text-secondary" aria-hidden />
                <CardTitle>Nâng cấp VIP</CardTitle>
                <CardDescription>Mở khoá toàn bộ bài học VIP, học không giới hạn.</CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild variant="secondary" size="sm">
                  <Link href={vipHref}>Xem gói VIP</Link>
                </Button>
              </CardContent>
            </Card>
          )}

          {profile && (
            <Card>
              <CardHeader>
                <UserRound className="size-6 text-primary" aria-hidden />
                <CardTitle>Hồ sơ của bạn</CardTitle>
                <CardDescription>Cập nhật họ tên, đổi mật khẩu, xem hạn VIP.</CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild variant="outline" size="sm">
                  <Link href="/profile">Mở hồ sơ</Link>
                </Button>
              </CardContent>
            </Card>
          )}
        </section>

        {profile && (
          <section>
            <Card className="border-dashed">
              <CardHeader>
                <Sparkles className="size-6 text-secondary" aria-hidden />
                <CardTitle>Gợi ý cho bạn</CardTitle>
                <CardDescription>
                  Sắp ra mắt — hệ thống sẽ gợi ý bài học tiếp theo dựa trên điểm số và chủ đề bạn
                  đang theo đuổi.
                </CardDescription>
              </CardHeader>
            </Card>
          </section>
        )}
      </main>
    </div>
  );
}
