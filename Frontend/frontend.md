# Frontend — Technical Document

**Project:** English Self-Study Platform (PBL6)
**Stack:** Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS · TanStack Query
**Owners:** Long (auth + payment flows) · Hà (learning pages) · Ninthanon (UI kit, admin console, notification center)

---

## 1. Scope

One Next.js application serving three audiences, separated by route group:

| Route group | Audience | Owner |
|---|---|---|
| `(marketing)` | Guests — landing, pricing, public lesson previews | Ninthanon |
| `(app)` | Students — lessons, quizzes, history, favorites, profile, VIP checkout | Hà, Long |
| `(admin)` | Editors and admins — content CRUD, moderation queue, user management, dashboard | Ninthanon |

The backend is the FastAPI gateway described in [backend.md](../Backend/backend.md). The frontend never talks to a business service directly — every request goes through the gateway.

---

## 2. Technology Choices

| Concern | Choice | Reason |
|---|---|---|
| Framework | Next.js 15, App Router | Server Components let lesson pages render on the server, which is what makes the LCP < 2.5s target (task T45) achievable |
| Language | TypeScript, `strict: true` | The compile step is the primary CI gate |
| Styling | Tailwind CSS v4 | No CSS-file coordination between three people touching the same screens |
| Components | shadcn/ui, copied into `src/components/ui` | This *is* the UI kit of task T51 — owned code, not a dependency to fight |
| Server state | TanStack Query v5 | Caching, retry and the polling needed for the eventual-consistency VIP flow |
| Client state | Zustand | Only for genuinely client-side state: quiz in-progress answers, sidebar, toasts |
| Forms | React Hook Form + Zod | One Zod schema validates the form and types the request body |
| HTTP | `fetch` wrapped in `src/lib/api-client.ts` | Central place for auth headers, refresh-on-401 and error normalisation |
| Icons | lucide-react | |
| Tests | Vitest + React Testing Library | |
| Lint / format | ESLint (`next/core-web-vitals`) + Prettier | |
| Package manager | npm (`package-lock.json` committed) | Simplest for a five-person student team |

---

## 3. Directory Layout

```
Frontend/
├── package.json
├── next.config.ts
├── tsconfig.json
├── eslint.config.mjs
├── vitest.config.ts
├── Dockerfile
├── .env.example
├── public/
└── src/
    ├── app/
    │   ├── layout.tsx                 # root layout, providers, fonts
    │   ├── (marketing)/
    │   │   ├── page.tsx               # landing
    │   │   └── pricing/page.tsx
    │   ├── (auth)/
    │   │   ├── login/page.tsx         # T32
    │   │   ├── register/page.tsx
    │   │   └── forgot-password/page.tsx
    │   ├── (app)/
    │   │   ├── layout.tsx             # requires session
    │   │   ├── categories/page.tsx    # T44
    │   │   ├── lessons/[id]/page.tsx  # T45
    │   │   ├── quiz/[id]/page.tsx     # T46
    │   │   ├── history/page.tsx       # T50
    │   │   ├── favorites/page.tsx
    │   │   ├── notifications/page.tsx # T56
    │   │   ├── profile/page.tsx
    │   │   └── checkout/
    │   │       ├── page.tsx           # T33 plan selection
    │   │       └── result/page.tsx    #     handles VIP-not-yet-applied
    │   ├── (admin)/
    │   │   ├── layout.tsx             # requires admin|editor
    │   │   ├── lessons/               # T52
    │   │   ├── users/                 # T53
    │   │   ├── moderation/            # T54
    │   │   └── dashboard/             # T55
    │   └── api/auth/[...]/route.ts    # route handlers that set httpOnly cookies
    ├── components/
    │   ├── ui/                        # UI kit — button, input, table, modal, toast...
    │   ├── layout/                    # header, sidebar, admin shell
    │   └── feature/                   # lesson-card, quiz-runner, vip-badge...
    ├── lib/
    │   ├── api-client.ts              # fetch wrapper + refresh handling
    │   ├── session.ts                 # server-side session read
    │   └── utils.ts
    ├── hooks/                         # useLessons, useQuizSubmit, useNotifications...
    ├── types/
    │   └── api.ts                     # types generated from the gateway OpenAPI schema
    └── styles/globals.css
```

**Convention:** a component in `components/ui` may not import from `hooks/` or `lib/api-client`. UI-kit components take props and emit events — nothing else. This is what allows Ninthanon to build them before the APIs exist.

---

## 4. Rendering Strategy

| Page | Strategy | Reason |
|---|---|---|
| Landing, pricing | Static | No user data |
| Category list, lesson list | Server Component + `revalidate: 60` | Public, cacheable, good for SEO |
| Lesson detail | Server Component, streamed | Text renders immediately; audio and images lazy-load below the fold (T45) |
| Quiz runner | Client Component | Fully interactive, holds answer state |
| Admin screens | Client Components with TanStack Query | Tables, filters and mutations; no SEO value |
| Checkout result | Client Component with polling | Must handle VIP lagging behind payment |

Images use `next/image` with explicit `width`/`height` to avoid layout shift. Lesson audio uses a native `<audio preload="none">` and only loads on interaction.

---

## 5. Authentication

Tokens are **never** put in `localStorage`. The flow:

1. The login form posts to `/api/auth/login`, a Next.js route handler.
2. The route handler calls the gateway, receives the access and refresh tokens, and writes them as `httpOnly`, `Secure`, `SameSite=Lax` cookies.
3. Server Components read the session with `lib/session.ts` and pass user context down.
4. Client-side requests go through `api-client.ts`, which sends cookies automatically.
5. On a `401`, `api-client` calls `/api/auth/refresh` once, then retries the original request. A second failure clears the cookies and redirects to `/login`.

Route protection lives in `middleware.ts`: unauthenticated users hitting `(app)` or `(admin)` are redirected to `/login?next=<path>`; a student hitting `(admin)` gets `/403`.

Content gating (task T47) is enforced **server-side**. The gateway already returns only a teaser for a VIP lesson requested by a non-VIP user. The frontend renders whatever it receives and shows an upgrade prompt when `lesson.locked === true` — it never hides content that was actually delivered to the browser.

---

## 6. Data Fetching Conventions

```ts
// hooks/use-lessons.ts
export function useLessons(params: LessonQuery) {
  return useQuery({
    queryKey: ["lessons", params],
    queryFn: () => api.get<Paginated<Lesson>>("/lessons", { params }),
    staleTime: 60_000,
  });
}
```

- Query keys are arrays starting with the resource name: `["lessons", params]`, `["lesson", id]`.
- Mutations invalidate by prefix: after creating a lesson, `invalidateQueries({ queryKey: ["lessons"] })`.
- Every error surfaces through a shared `<ErrorBoundary>` plus a toast. The `error.code` from the backend envelope maps to a Vietnamese message in `lib/error-messages.ts`.

### The VIP eventual-consistency case (T33)

After the payment gateway redirects back, `/checkout/result` polls `GET /users/me` every 2s for up to 10s. While `tier !== "vip"` it shows "Đang xử lý thanh toán…". If the window elapses it shows a message telling the user their VIP will activate shortly, with a manual refresh button — it never shows a failure, because the payment did succeed.

---

## 7. Environment Configuration

```env
# .env.example
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080/api/v1
NEXT_PUBLIC_CDN_BASE_URL=https://cdn.example.com
API_INTERNAL_URL=http://gateway:8000/api/v1   # server-side, container network
SESSION_COOKIE_NAME=pbl6_session
```

Anything prefixed `NEXT_PUBLIC_` is embedded in the browser bundle — never put a secret behind that prefix.

---

## 8. Local Development

```bash
cd Frontend
cp .env.example .env.local
npm ci
npm run dev          # http://localhost:3000
```

The backend must be running (`cd Backend && docker compose up -d`). Regenerate API types after any backend contract change:

```bash
npm run gen:api      # openapi-typescript from the gateway schema -> src/types/api.ts
```

### Scripts

| Script | Purpose |
|---|---|
| `npm run dev` | Dev server with hot reload |
| `npm run build` | Production build — **this is the compile-error gate** |
| `npm run start` | Serve the production build |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run format:check` | Prettier verification |
| `npm run test` | Vitest, single run |
| `npm run gen:api` | Regenerate types from the gateway OpenAPI schema |

---

## 9. Quality Gates

Enforced by [frontend-ci.yml](../.github/workflows/frontend-ci.yml) on every push and pull request touching `Frontend/**`:

```
  typecheck       tsc --noEmit               fails fast on a compile error
     |
     v
  quality         eslint + prettier --check
     |
     v
  test            vitest run
     |
     v
  build           next build
     |
     v
  docker          docker build (not pushed on PRs)
```

`typecheck` runs first and alone because it is the cheapest way to catch the most common breakage — a renamed API field. `next build` also type-checks, but it takes far longer to tell you.

### What to test

- UI-kit components: render and interaction (Vitest + RTL).
- Hooks with non-trivial logic: quiz scoring display, VIP polling.
- Pages are **not** unit-tested — they are covered by the Newman E2E suite (task T58).

---

## 10. Performance Targets

| Metric | Target | How |
|---|---|---|
| LCP (lesson detail) | < 2.5s | Server-rendered text, `next/image` with `priority` on the hero only, `preload="none"` audio |
| CLS | < 0.1 | Explicit dimensions on every image; skeletons match final layout size |
| JS bundle (initial, app routes) | < 200 KB gzipped | Server Components by default; `"use client"` only where needed; `next/dynamic` for the quiz runner and charts |
| TTFB | < 500ms | `revalidate` on public list pages |

Check with `npm run build` — it prints per-route bundle sizes. A route crossing 200 KB needs a reason in the PR description.

---

## 11. Conventions

- Files `kebab-case.tsx`, components `PascalCase`, hooks `useCamelCase`.
- No `any`. Use `unknown` and narrow it.
- No inline `fetch` in a component — go through `api-client`.
- No hardcoded colours — use Tailwind tokens from the theme.
- User-facing copy is Vietnamese; code, comments and commit messages are English.
- Branch `feat/<task-id>-<slug>` (e.g. `feat/T44-category-page`), PR title `[T44] Category listing page`.

---

## 12. Known Risks

| Risk | Mitigation |
|---|---|
| Three people editing shared UI-kit components | UI kit (T51) is frozen after Sprint 0; changes to it need a PR review from Long or Hà |
| Backend contracts still moving | `npm run gen:api` regenerates types; a breaking change surfaces as a `typecheck` failure in CI rather than a runtime bug |
| Admin dashboard (T55) depends on the gateway stats API (T11) | Build against a static fixture first; swap in the real hook when T11 lands |
| Payment sandbox unavailable at demo time | The backend's `MOCK_PAYMENT` flag returns a fake redirect URL; the frontend needs no change |
