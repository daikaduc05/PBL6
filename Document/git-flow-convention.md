# Quy ước Git Flow

Mô hình 4 tầng: `feature/*` → `module/*` → `develop` → `main`

---

## 1. Các loại nhánh

| Nhánh | Vòng đời | Tách ra từ | Merge vào | Ai được push trực tiếp |
|---|---|---|---|---|
| `main` | Vĩnh viễn | – | – | Không ai (chỉ qua PR) |
| `develop` | Vĩnh viễn | `main` | `main` | Không ai (chỉ qua PR) |
| `module/<ten-module>` | Dài hạn | `develop` | `develop` | Người phụ trách module |
| `feature/<module>/<mo-ta>` | Ngắn hạn | `module/<ten-module>` | `module/<ten-module>` | Người viết feature |
| `fix/<module>/<mo-ta>` | Ngắn hạn | `module/<ten-module>` | `module/<ten-module>` | Người sửa |
| `hotfix/<mo-ta>` | Ngắn hạn | `main` | `main` **và** `develop` | Người sửa |

### Ý nghĩa

- **`main`** — code đang chạy production. Mỗi commit trên `main` phải tương ứng với một tag phiên bản.
- **`develop`** — code tích hợp của tất cả module. Luôn build được và chạy được toàn hệ thống.
- **`module/*`** — mỗi module/service có một nhánh riêng, do một người sở hữu. Mọi thay đổi của module đó đi qua đây trước khi lên `develop`.
- **`feature/*`** — một đơn vị công việc nhỏ, sống không quá vài ngày.

---

## 2. Quy tắc đặt tên

```
module/account
module/gateway
module/notification

feature/account/register-api
feature/content/lesson-crud
feature/payment/vnpay-webhook

fix/learning/quiz-score-rounding
hotfix/token-expired-500
```

Quy tắc chung:

- Chữ thường, phân tách bằng dấu `-` (kebab-case), không dấu tiếng Việt.
- Tối đa ~5 từ mô tả.
- Nếu có issue tracker, thêm mã ở cuối: `feature/account/register-api-42`.

---

## 3. Luồng làm việc chuẩn

### 3.1. Khởi tạo module (một lần)

```bash
git checkout develop
git pull origin develop
git checkout -b module/account
git push -u origin module/account
```

### 3.2. Làm một feature

```bash
git checkout module/account
git pull origin module/account
git checkout -b feature/account/register-api

# ... code, commit nhiều lần ...

git push -u origin feature/account/register-api
```

Sau đó mở PR: `feature/account/register-api` → `module/account`.

### 3.3. Đồng bộ trước khi merge

Trước khi mở PR, luôn cập nhật nhánh nền để tự xử lý conflict:

```bash
git checkout feature/account/register-api
git fetch origin
git rebase origin/module/account
# xử lý conflict nếu có
git push --force-with-lease
```

> Chỉ dùng `--force-with-lease`, **không bao giờ** dùng `--force`.
> Chỉ được rebase nhánh feature của riêng mình, không rebase `module/*`, `develop`, `main`.

### 3.4. Đưa module lên develop

Khi module hoàn thành một phần chức năng chạy được và test pass:

```bash
git checkout module/account
git pull origin develop --no-rebase   # lấy thay đổi mới nhất của hệ thống
# chạy test
git push origin module/account
```

Mở PR: `module/account` → `develop`.

### 3.5. Release lên main

```bash
# PR: develop -> main
# sau khi merge:
git checkout main
git pull origin main
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

### 3.6. Hotfix

```bash
git checkout main
git pull origin main
git checkout -b hotfix/token-expired-500
# ... sửa ...
```

Merge vào `main` → tag phiên bản patch (`v1.2.1`) → **merge ngược về `develop`** ngay trong ngày. Nếu module nào bị ảnh hưởng, chủ module tự pull `develop` về nhánh module của mình.

---

## 4. Chiến lược merge

| Hướng merge | Cách merge | Lý do |
|---|---|---|
| `feature/*` → `module/*` | **Squash merge** | Gộp commit lặt vặt thành 1 commit sạch |
| `module/*` → `develop` | **Merge commit** (`--no-ff`) | Giữ lịch sử theo module, dễ revert cả cụm |
| `develop` → `main` | **Merge commit** (`--no-ff`) | Đánh dấu rõ ranh giới release |
| `hotfix/*` → `main`, `develop` | **Merge commit** | Giữ nguyên vết sửa lỗi |

Xoá nhánh `feature/*` và `fix/*` ngay sau khi merge.

---

## 5. Quy ước commit message

Theo Conventional Commits:

```
<type>(<scope>): <mô tả ngắn, thể mệnh lệnh>
```

**type**: `feat` | `fix` | `refactor` | `docs` | `test` | `chore` | `perf` | `style`
**scope**: tên module (`account`, `gateway`, `payment`...)

Ví dụ:

```
feat(account): add refresh token endpoint
fix(payment): handle duplicate webhook callback
chore(gateway): bump nestjs to 10.4
refactor(learning): extract quiz scoring into service
```

Quy tắc:

- Dòng đầu ≤ 72 ký tự, không kết thúc bằng dấu chấm.
- Tiếng Anh, chữ thường sau dấu `:`.
- Breaking change: thêm `!` → `feat(account)!: change login response shape`.

---

## 6. Quy tắc Pull Request

- **Bắt buộc PR** cho mọi merge vào `module/*`, `develop`, `main`. Không push trực tiếp.
- Tối thiểu **1 người review approve**; PR vào `main` cần **2 approve**.
- CI (build + lint + test) phải xanh mới được merge.
- PR không quá ~400 dòng thay đổi. Lớn hơn thì tách nhỏ.
- Mô tả PR gồm: mục đích, phạm vi ảnh hưởng, cách test.
- Người mở PR là người bấm merge (sau khi được approve).

---

## 7. Branch protection cần bật trên remote

**`main`**
- Chặn push trực tiếp và force push
- Yêu cầu PR + 2 approve + CI pass
- Yêu cầu nhánh cập nhật với base trước khi merge
- Chặn xoá nhánh

**`develop`**
- Chặn push trực tiếp và force push
- Yêu cầu PR + 1 approve + CI pass

**`module/*`**
- Chặn force push
- Yêu cầu PR + 1 approve

---

## 8. Những điều cấm

- Push trực tiếp lên `main` hoặc `develop`.
- Rebase hoặc force push nhánh dùng chung (`module/*`, `develop`, `main`).
- Merge `feature` của module A thẳng vào `module/B` hoặc thẳng vào `develop`.
- Commit file `.env`, secret, key, file build, `node_modules`.
- Để nhánh feature sống quá 1 tuần mà không đồng bộ với nhánh nền.
- Commit message kiểu `update`, `fix bug`, `abc`, `.`.

---

## 9. Sơ đồ tổng quát

```
main        ──●───────────────────────●──────────●──►  (tag v1.0.0, v1.1.0, v1.1.1)
               \                     /          /
                \                   /          / hotfix/*
develop     ─────●────●────●───────●──────────●─────►
                  \    \    \     /
                   \    \    \   / module/content
module/account ─────●────●────●─┘
                     \    \
                      \    \ feature/account/login-api
                       \
                        feature/account/register-api
```
