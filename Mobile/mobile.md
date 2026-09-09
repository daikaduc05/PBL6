# Mobile — Technical Document

**Project:** English Self-Study Platform (PBL6)
**Stack:** React Native (Expo SDK 52+) · Expo Router · TypeScript · TanStack Query
**Platforms:** Android and iOS from one codebase
**Status:** Not in the original assignment sheet. Scope and ownership below are a proposal — confirm with the team before Sprint 2.

---

## 1. Scope

The mobile app is a **student client only**. It deliberately does not include the editor or admin console — those stay on the web ([frontend.md](../Frontend/frontend.md)).

**In scope**
- Register / login / logout, profile
- Browse categories and lessons, filter by level
- Lesson detail with audio playback
- Take a quiz and see the score
- Attempt history and favorites
- Push notifications for the 20:00 study reminder
- VIP upgrade (opens the payment gateway in a browser session)

**Out of scope**
- Content authoring, moderation, user administration, the statistics dashboard
- Offline lesson download (a stretch goal — see §9)

It consumes the same FastAPI gateway as the web app; no mobile-only backend endpoints are needed.

---

## 2. Technology Choices

| Concern | Choice | Reason |
|---|---|---|
| Framework | Expo SDK 52+ (managed workflow) | No Xcode/Android Studio needed for day-to-day work; EAS handles builds |
| Language | TypeScript, `strict: true` | Shares API types with the web app |
| Navigation | Expo Router v4 | File-based routing, the same mental model as Next.js |
| Server state | TanStack Query v5 | Same library and query-key conventions as the web app |
| Client state | Zustand | Quiz answers in progress, audio player state |
| Styling | NativeWind v4 | Tailwind class names, so web and mobile share a design vocabulary |
| HTTP | `fetch` wrapped in `lib/api-client.ts` | Mirrors the web client, minus cookies |
| Token storage | `expo-secure-store` | Keychain / Keystore — never `AsyncStorage` for tokens |
| Audio | `expo-audio` | Lesson playback with background support |
| Push | `expo-notifications` + Expo Push Service | Receives the study reminder |
| Forms | React Hook Form + Zod | Same schemas as web where the shape matches |
| Tests | Jest + `@testing-library/react-native` | |
| Lint / format | ESLint (`eslint-config-expo`) + Prettier | |
| Build / release | EAS Build + EAS Update | OTA updates for JS-only changes |

---

## 3. Directory Layout

```
Mobile/
├── app.json                    # Expo config: name, slug, icons, plugins
├── eas.json                    # build profiles: development / preview / production
├── package.json
├── tsconfig.json
├── .env.example
├── assets/
└── src/
    ├── app/                    # Expo Router — file-based routes
    │   ├── _layout.tsx         # root: providers, fonts, auth gate
    │   ├── (auth)/
    │   │   ├── login.tsx
    │   │   └── register.tsx
    │   └── (tabs)/
    │       ├── _layout.tsx     # bottom tab bar
    │       ├── index.tsx       # Home — recommended lessons
    │       ├── categories/
    │       │   ├── index.tsx
    │       │   └── [id].tsx
    │       ├── lessons/[id].tsx
    │       ├── quiz/[id].tsx
    │       ├── notifications.tsx
    │       └── profile.tsx
    ├── components/
    │   ├── ui/                 # Button, Card, Input, Sheet, Skeleton...
    │   └── feature/            # LessonCard, AudioPlayer, QuizQuestion, VipBadge
    ├── lib/
    │   ├── api-client.ts
    │   ├── auth-store.ts       # secure-store wrapper + Zustand
    │   ├── notifications.ts    # permission request, token registration
    │   └── query-client.ts
    ├── hooks/
    └── types/api.ts            # generated from the gateway OpenAPI schema
```

---

## 4. Navigation Map

```
Root
├── (auth)            unauthenticated only
│   ├── login
│   └── register
└── (tabs)            authenticated
    ├── Home          recommended lessons  ->  GET /lessons/recommended
    ├── Learn         categories -> lessons -> lesson detail -> quiz
    ├── Activity      attempt history + favorites
    ├── Alerts        notification list
    └── Profile       account info, VIP status, upgrade, logout
```

The root layout reads the stored token on launch and redirects to `(auth)` or `(tabs)` before the splash screen hides, so there is no visible flash of the wrong screen.

---

## 5. Authentication

The web app uses `httpOnly` cookies; mobile cannot, so it holds tokens directly:

1. Login posts to `/api/v1/auth/login` and receives `{ access_token, refresh_token, expires_in }`.
2. Both tokens go into `expo-secure-store` (Keychain on iOS, Keystore on Android).
3. `api-client` attaches `Authorization: Bearer <access_token>` to every request.
4. On a `401`, it calls `/api/v1/auth/refresh` **once**, stores the rotated pair and retries. A second failure clears secure storage and routes to `/login`.
5. Concurrent 401s share a single in-flight refresh promise, so five parallel requests do not trigger five refreshes.

Logout clears secure storage, resets the TanStack Query cache and unregisters the push token.

---

## 6. Push Notifications

1. After login, the app requests notification permission (not at first launch — permission asked in context converts far better).
2. It obtains an Expo push token and sends it to the backend: `POST /api/v1/notifications/devices` with `{ expo_push_token, platform }`.
3. The notification service stores the token against the user and sends the 20:00 reminder through the Expo Push API alongside the existing email channel.
4. Tapping a notification deep-links via Expo Router — e.g. a reminder opens the Home tab, a lesson-published alert opens that lesson.
5. On logout, the app calls `DELETE /api/v1/notifications/devices/{token}`.

**Backend change required:** a `device_tokens` table in `notification_db` and an Expo push channel in the notification service. This is additional work for Đạt, not covered by the current sheet — budget roughly 2 person-days.

---

## 7. Offline and Media Behaviour

- Lesson **lists** are cached by TanStack Query with `staleTime: 5min` and persisted with `@tanstack/query-async-storage-persister`, so the app opens with content on a cold, offline start.
- Lesson **audio** streams from the CDN. `expo-audio` is configured with `staysActiveInBackground: true` so playback survives a screen lock.
- Quiz submission is **online only**. If the network drops mid-quiz, answers stay in Zustand and the submit button retries; nothing is lost by backgrounding the app.
- Images use `expo-image` with `cachePolicy: "memory-disk"`.

---

## 8. Environment Configuration

```env
# .env.example  (consumed via app.config.ts -> expo-constants)
EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8080/api/v1   # Android emulator -> host machine
EXPO_PUBLIC_CDN_BASE_URL=https://cdn.example.com
```

Note the host address: a physical device needs your machine's LAN IP, the Android emulator needs `10.0.2.2`, and the iOS simulator can use `localhost`. Everything prefixed `EXPO_PUBLIC_` is visible in the shipped bundle — never a secret.

---

## 9. Local Development

```bash
cd Mobile
cp .env.example .env
npm ci
npx expo start          # press "a" for Android, "i" for iOS, or scan the QR code
```

The backend must be reachable from the device (`cd Backend && docker compose up -d`, and the phone on the same Wi-Fi).

| Script | Purpose |
|---|---|
| `npx expo start` | Metro bundler |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run test` | Jest |
| `npx expo-doctor` | Verifies native dependency versions match the SDK |
| `eas build -p android --profile preview` | Installable APK for the demo |

---

## 10. Build and Release

| Profile | Output | Use |
|---|---|---|
| `development` | Dev client | Day-to-day work with custom native modules |
| `preview` | APK / internal `.ipa` | What the team and the reviewers install |
| `production` | AAB / App Store build | Only if the project is actually published |

For the defence demo, `eas build -p android --profile preview` produces an APK that can be installed directly — no Play Store account needed. JS-only fixes after that can ship through `eas update` without a rebuild.

**No CI pipeline is configured for Mobile.** Backend and frontend have one because they gate merges to shared services; the mobile app is a single-owner client where `expo-doctor` plus a local `npm run typecheck` is sufficient at this stage. Add an EAS Build workflow if a second developer joins the app.

---

## 11. Conventions

Same as the web app so people can move between the two: `kebab-case` files, `PascalCase` components, `useCamelCase` hooks, no `any`, TanStack query keys as `["resource", params]`, Vietnamese user-facing copy, English code and commits, branches `feat/<task-id>-<slug>`.

Mobile-specific:
- Every touch target ≥ 44×44 pt.
- Wrap screens in `SafeAreaView` — do not hardcode status-bar padding.
- Use `FlatList` for any list that can exceed ~20 items, never `.map()` inside a `ScrollView`.
- Test on a real Android device before opening a PR; the emulator hides scroll and audio problems.

---

## 12. Known Risks

| Risk | Mitigation |
|---|---|
| Mobile is not in the assignment sheet, so no person-days are allocated | Confirm ownership and scope before Sprint 2, or explicitly defer the app to after the defence |
| Push notifications need backend work not in the plan | Either budget ~2 days for Đạt, or ship v1 with in-app notifications only |
| iOS builds need a paid Apple Developer account | Demo on Android; keep the iOS build as a stretch goal |
| VIP purchase inside a mobile app can breach app-store payment rules | Not an issue for an APK-only demo. If the app is ever published, the upgrade flow must move to the website |
| Device cannot reach a `localhost` backend | Documented in §8; use the LAN IP or an `ngrok` tunnel |
