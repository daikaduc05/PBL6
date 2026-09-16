# Design System — PBL6 English Self-Study Platform

Shared UI rules for **Web** ([frontend.md](../Frontend/frontend.md)) and **Mobile**
([mobile.md](../Mobile/mobile.md)). One visual language, two Tailwind engines:

| Platform | Engine | Token source |
|---|---|---|
| Web (Next.js) | Tailwind CSS v4 (`@theme`) | [tokens.css](tokens.css) → `Frontend/src/styles/globals.css` |
| Mobile (Expo) | NativeWind v4 | [tailwind.config.mobile.js](tailwind.config.mobile.js) → `Mobile/tailwind.config.js` |

Both files encode the **same values** below. Never hand-pick a color, radius or
spacing value outside this system — this is what `frontend.md`'s "no hardcoded
colours" rule and `mobile.md`'s "same design vocabulary" line mean in practice.

---

## 1. Brand personality

Approachable and encouraging, not corporate; academic enough to feel credible.
Confident indigo for structure, warm amber for reward (VIP, streaks, correct
answers) — the app should feel like a tutor, not a spreadsheet.

---

## 2. Color

### Brand & semantic tokens (light)

| Token | Hex | Use |
|---|---|---|
| `primary` | `#4F46E5` | Primary actions, links, active nav, focus |
| `primary-hover` | `#4338CA` | Hover/active state of primary |
| `primary-foreground` | `#FFFFFF` | Text/icon on `primary` |
| `secondary` | `#F59E0B` | VIP badge, streaks, highlights — **never** for primary CTAs |
| `secondary-foreground` | `#1C1917` | Text/icon on `secondary` |
| `success` | `#16A34A` | Correct answer, passed quiz, payment success |
| `danger` | `#DC2626` | Wrong answer, errors, locked/destructive |
| `warning` | `#D97706` | Non-blocking caution (e.g. "VIP expiring soon") |
| `info` | `#0284C7` | Neutral notices, in-progress payment |
| `background` | `#FFFFFF` | Page background |
| `surface` | `#F8FAFC` | Cards, inputs |
| `surface-2` | `#F1F5F9` | Nested surfaces, table header, hover row |
| `border` | `#E2E8F0` | Dividers, input borders |
| `text` | `#0F172A` | Primary text |
| `text-muted` | `#64748B` | Secondary text, placeholders, timestamps |
| `ring` | `#4F46E5` | Focus ring (always visible, never removed) |

Dark-mode equivalents are in [tokens.css](tokens.css) `.dark {}`. Dark mode is
**token-complete but not required for the defence demo** — light is the
default; ship it if time allows, don't block on it.

### Rules

- Every color a component uses must be one of the tokens above — referenced by
  name (`bg-primary`, `text-text-muted`), never a raw hex or a bare Tailwind
  color (`bg-indigo-600`, `text-slate-500`) in `components/feature` or
  `app/`. Raw Tailwind colors are only acceptable inside `components/ui`
  primitives while a token doesn't exist yet — flag it in the PR.
- `secondary` (amber) is reserved for VIP/reward context. A second brand color
  used as a generic CTA reads as "sale banner," not "premium."
- Minimum contrast: 4.5:1 for body text, 3:1 for large text (≥18px) and icons.

---

## 3. Typography

**Font:** Inter (Google Fonts) — full Vietnamese diacritic coverage, free,
variable weight. Web via `next/font/google`; mobile via
`@expo-google-fonts/inter`.

| Style | Size / Line-height | Weight | Use |
|---|---|---|---|
| `display` | 36px / 40px | 700 | Landing hero only |
| `h1` | 30px / 36px | 700 | Page title |
| `h2` | 24px / 32px | 600 | Section title |
| `h3` | 20px / 28px | 600 | Card title, modal title |
| `body-lg` | 18px / 28px | 400 | Lesson body text |
| `body` | 16px / 24px | 400 | Default UI text |
| `body-sm` | 14px / 20px | 400 | Secondary text, form labels |
| `caption` | 12px / 16px | 500 | Timestamps, badges, helper text |
| `button` | 14–16px / 20–24px | 500 | Button labels — never 400 |

Rules: one `<h1>` per page; never skip a heading level for style (use size
tokens, not heading tags, to change visual weight); no justified text; body
text max width ~72ch for readability on lesson pages.

---

## 4. Spacing & layout

4px base unit — use Tailwind's default scale (`p-1`…`p-16`) directly, no
custom scale needed. Prefer multiples of 4; arbitrary values (`p-[13px]`) are
a review flag.

| Context | Value |
|---|---|
| Component internal padding (button, input) | 8–12px vertical, 16px horizontal |
| Card padding | 16px (mobile) / 24px (web) |
| Section gap (stacked cards, list items) | 12–16px |
| Page gutter | 16px (mobile), 24px (web `sm`), 32px (web `lg+`) |
| Max content width (reading content) | `max-w-3xl` (lesson body), `max-w-6xl` (dashboards) |

Breakpoints: Tailwind defaults (`sm` 640 / `md` 768 / `lg` 1024 / `xl` 1280 /
`2xl` 1536). Don't invent new ones.

---

## 5. Radius & elevation

| Token | Value | Use |
|---|---|---|
| `radius-sm` | 6px | Inputs, small badges, checkboxes |
| `radius-md` | 10px | Buttons, default cards |
| `radius-lg` | 16px | Modals, sheets, large cards |
| `radius-full` | 9999px | Avatars, pills, VIP badge |

| Elevation | CSS | Use |
|---|---|---|
| `shadow-sm` | `0 1px 2px rgb(0 0 0 / 0.05)` | Cards at rest |
| `shadow-md` | `0 4px 12px rgb(0 0 0 / 0.10)` | Dropdown, popover |
| `shadow-lg` | `0 12px 32px rgb(0 0 0 / 0.16)` | Modal, sheet |

Mobile has no native box-shadow spec — use `elevation` (Android) /
`shadowOpacity` (iOS) at equivalent visual weight, or a library that maps
Tailwind shadow classes for you (NativeWind supports `shadow-sm/md/lg` out of
the box on iOS; Android needs `elevation-*` alongside it).

---

## 6. Iconography

**lucide-react** on web (already chosen in `frontend.md`), **lucide-react-native**
on mobile — same icon set, same names, so a component ported between platforms
needs no icon swap.

- Stroke width 2px, sizes 16 / 20 / 24px only.
- Decorative icons: `aria-hidden` (web) / no accessibility role (mobile).
- Icon-only buttons must have an accessible label (`aria-label` / `accessibilityLabel`).

---

## 7. Motion

- Hover/press feedback: 150ms ease-out.
- Modal/sheet open-close: 200–250ms ease-out, slide or fade, never both at
  full distance (keep it subtle).
- Respect `prefers-reduced-motion` on web; keep mobile transitions short
  enough that they don't need a reduced-motion switch.

---

## 8. Component rules (cheat sheet)

Full components live in `components/ui` (web) and `src/components/ui`
(mobile) — task T51, owned by Ninthanon, frozen after Sprint 0. This is the
contract other components rely on.

| Component | Rule |
|---|---|
| **Button** | Variants: `primary`, `secondary`, `outline`, `ghost`, `destructive`, `link`. Sizes: `sm` (32px h), `md` (40px h), `lg` (48px h). Disabled = 50% opacity + no pointer events. Loading = spinner replaces label, width unchanged (no layout shift). |
| **Input** | Height 40px (md). Border `border`, focus → 2px `ring` offset 2px. Error state: `danger` border + helper text in `danger` below, never only a red border with no text. |
| **Card** | `surface` bg, 1px `border`, `radius-lg`, `shadow-sm`. |
| **Badge** | `radius-full`, `caption` text, variants match semantic tokens; **VIP badge** = `secondary` gradient + crown icon, not a plain badge. |
| **Modal / Sheet** | Overlay `black/50%`, panel `surface` + `radius-lg` + `shadow-lg`. Closes on `Esc` and overlay click (web); swipe-down on mobile sheets. |
| **Toast** | 4 variants = semantic tokens. Auto-dismiss 4s. Bottom-right on web, top on mobile (clears the tab bar). |
| **Skeleton** | `surface-2` + pulse. Must match the exact pixel dimensions of the real content — this is the CLS budget in `frontend.md` §10. |
| **Lesson card** | 16:9 thumbnail, 2-line title clamp, level badge, VIP lock overlay when `is_free = false` and viewer isn't VIP. |
| **Quiz option** | Pill-shaped selectable row. States: default → selected (`primary` border) → after submit: correct (`success` bg) / incorrect (`danger` bg). Never reveal correctness before submit. |
| **Table** (admin only) | Header `surface-2`, row hover `surface-2`, sticky header on scroll. |

---

## 9. Accessibility & platform baselines

- Focus-visible ring on every interactive element — never `outline: none`
  without a replacement.
- Touch targets ≥ 44×44pt everywhere, web included (not just mobile.md's rule).
- Color is never the only signal — pair `success`/`danger` with an icon or text
  (quiz results, transaction status).
- `alt` text on every meaningful image; decorative images `alt=""`.

---

## 10. Content

- User-facing copy: **Vietnamese**, sentence case, second person "bạn."
- Error messages are plain-language, never a raw backend error code (map
  `error.code` → Vietnamese string, per `frontend.md` §6).
- Currency: VND, dot thousands separator, `₫` suffix — `299.000₫`.
- Dates: `dd/MM/yyyy`; relative time ("2 giờ trước") for notifications/comments.

---

## 11. Governance

- `components/ui` is frozen after Sprint 0 (`frontend.md` §12) — a change needs
  review from Long or Hà, and if it changes a token in this doc, update
  [tokens.css](tokens.css) and [tailwind.config.mobile.js](tailwind.config.mobile.js)
  in the same PR so web and mobile never drift apart.
- New semantic token needed? Add it here first, then to both token files —
  don't invent a one-off color inside a single component.
