# Project Spec — Module M2: Notification Service & Recommendation Lesson

**Owner:** Đạt
**Service:** `notification` — port `8005`
**Database:** Supabase (shared PostgreSQL), schema `notification`
**Module branch:** `module/notification` (duy nhất)
**Tổng ước lượng:** 15 ngày công (T12–T19 theo `phan_cong_do_an_tu_hoc_tieng_anh (1).xlsx`)
**Tham chiếu:** `Backend/db/*.sql` (nguồn sự thật về schema), `Backend/db/README.md`, `git-flow-convention.md`

---

## 0. Quyết định nền tảng

### 0.1. Kiến trúc: microservice trên shared database

Năm bounded context chạy như năm service độc lập, nhưng **dùng chung một database Supabase**, mỗi service sở hữu một **schema** riêng (`00_schemas.sql`). Service `notification` sở hữu schema `notification`.

Hệ quả quan trọng nhất cho M2: **mọi dữ liệu của service khác đều nằm trong tầm với bằng SQL trực tiếp.** Đây là điều mà kiến trúc "database per service" không cho phép, và nó quyết định cách mảng Recommendation được xây (xem §0.4).

### 0.2. Nguồn sự thật về schema: Alembic, mỗi service một lịch sử

Schema do **Alembic** quản lý, giống account và content. Các file SQL trong `Backend/db/` chỉ là **baseline** ghi lại những gì đã tạo tay trên Supabase trước khi Alembic được dựng — không thêm file SQL mới nữa.

Mối lo "năm service dùng chung database sẽ tạo năm bảng `alembic_version` rải rác" được xử lý bằng `version_table_schema` trong `alembic/env.py`: mỗi service giữ bảng version **bên trong schema của chính nó**, hoàn toàn độc lập.

Migration của M2:

| Revision | Nội dung | Cách áp |
|---|---|---|
| `0001_baseline_notification` | `messages`, `settings` — mirror `05_notification.sql` | `alembic stamp 0001` (Supabase đã có) |
| `0002_processed_events` | `processed_events` | `alembic upgrade head` |

Database trống (CI, container test) bỏ qua bước stamp và chạy thẳng `upgrade head` — revision 0001 tự tạo schema.

**Một bẫy đã gặp:** `alembic/env.py` phải dùng `engine.begin()` chứ không phải `engine.connect()`. SQLAlchemy 2.0 rollback connection chưa commit khi thoát, nên với `connect()` toàn bộ migration bị huỷ âm thầm trong khi `alembic upgrade head` vẫn báo thành công. Service account hiện đang dùng `connect()` — cần báo Long/Đức.

### 0.3. Schema `notification` — bám đúng bản đã deploy

```sql
notification.messages
  id         uuid pk default gen_random_uuid()
  user_id    uuid not null          -- logical FK -> account.users.id
  title      text not null
  content    text not null
  is_read    boolean not null default false
  created_at timestamptz not null default now()
  -- index: (user_id, created_at desc) where is_read = false

notification.settings
  user_id               uuid pk    -- logical FK -> account.users.id
  enable_daily_reminder boolean not null default true
  device_token          text       -- Expo push token, dành cho mobile về sau

notification.processed_events        -- thêm ở 06_*.sql
  event_id     uuid pk              -- envelope.event_id
  event_type   text not null
  processed_at timestamptz not null default now()
```

**Vì sao phải thêm `processed_events`.** Outbox relay của payment là at-least-once — cùng một `payment.succeeded` sẽ được gửi lại khi có sự cố giữa publish và ack. Không có bảng dedupe thì user nhận thông báo "Đã kích hoạt VIP" hai lần. Consumer insert `event_id` trong **cùng transaction** với việc ghi message; bản trùng đụng primary key, transaction rollback, message được ack mà không để lại tác dụng phụ. Bảng này nằm trong schema của chính M2 nên không ảnh hưởng ai.

**Những gì schema hiện tại KHÔNG có — và cách sống chung (không đổi schema):**

| Thiếu | Ảnh hưởng | Cách xử lý |
|---|---|---|
| `messages.type` | FE không phân loại được thông báo để chọn icon / điều hướng | Chấp nhận. `title` đủ mô tả cho bản đồ án. Nếu T56 (Ninthanon) thực sự cần, thêm cột sau bằng file `07_*.sql` |
| Bảng `templates` | Không có template lưu DB | **Tốt hơn:** để template Jinja2 thành file trong code (`email/templates/`) — version control được, sửa cùng PR, không phải seed DB |
| `settings.email_enabled` | Không tách được kênh in-app và email | Một cờ `enable_daily_reminder` điều khiển cả hai kênh của cron nhắc học. Đơn giản hơn, vẫn đủ cho T13 ("bật/tắt nhận thông báo") |
| `settings.reminder_hour` | Không cho user chọn giờ nhắc | Cron cố định 20:00 cho mọi user — đúng nguyên văn T14 |

### 0.4. Đọc dữ liệu service khác: SQL read-only, qua một lớp cô lập

Recommendation cần `learning.histories` và `content.lessons`; cron nhắc học cần `account.users`. Hai lựa chọn:

- **Gọi HTTP API nội bộ của Hà/Long** — đúng chuẩn microservice, nhưng các endpoint đó chưa tồn tại và sẽ chặn Đạt hết Sprint 2.
- **Đọc trực tiếp bằng SQL** — khả thi vì shared database, không chặn ai.

**Chọn phương án 2**, kèm bốn ràng buộc bắt buộc:

1. **Chỉ `SELECT`.** Không bao giờ `INSERT`/`UPDATE`/`DELETE` vào schema của người khác. Ghi vào schema khác = phá vỡ quyền sở hữu, đây là lằn ranh không được vượt.
2. **Không `JOIN` cross-schema.** Query riêng từng schema rồi ghép trong Python. Giữ được tinh thần bounded context, và quan trọng hơn: mỗi query tương ứng một lời gọi API sau này.
3. **Cô lập vào đúng một file** — `recommendation/readers.py`. Không rải SQL cross-schema khắp codebase.
4. **Interface ổn định.** Khi Hà xong endpoint nội bộ, chỉ thay thân hàm trong `readers.py`, phần còn lại không đổi một dòng.

Đây là nợ kỹ thuật **có chủ đích và có lối ra**, không phải đi tắt. Ghi rõ trong README của service.

### 0.5. Vì sao chỉ một nhánh module

Trước đây nhóm tạo hai nhánh `module/NotificationService` và `module/RecommendationLesson`. Đã gộp thành `module/notification` vì:

| Lý do | Giải thích |
|---|---|
| Convention định nghĩa module = service | `git-flow-convention.md`: mỗi module/service một nhánh, do **một người** sở hữu. Recommendation là thư mục con trong `services/notification/`, không phải service. |
| Cùng một owner | Cả hai đều của Đạt. Nhánh module để cô lập quyền sở hữu **giữa những người khác nhau**, không phải để phân loại việc của cùng một người. |
| Conflict trên file dùng chung | Hai nhánh cùng sửa `main.py`, `config.py`, `models.py`, `pyproject.toml`, `Dockerfile` → merge nào cũng conflict. |

Lệnh đã chạy:

```bash
git branch -m module/RecommendationLesson module/recommendation
git branch -m module/NotificationService module/notification
git branch -d module/recommendation
```

An toàn vì khi đó hai nhánh cùng commit và chưa push lên remote.

Phân loại công việc bằng **tiền tố trong tên feature branch**, không bằng nhánh module:

```
feature/notification/db-schema             ← mảng A
feature/notification/reco-rule-based-api   ← mảng B, tiền tố "reco-"
```

---

## 0.6. Bảng task ↔ feature branch

Tất cả tách ra từ và merge về `module/notification`.

| Task | Sprint | Ước lượng | Feature branch | Mảng |
|---|---|---|---|---|
| T12 — Skeleton + models + config | 1 | 1d | `feature/notification/service-skeleton` | A |
| T13 — API thông báo | 1 | 2d | `feature/notification/notification-api` | A |
| T15 — Email channel | 2 | 2d | `feature/notification/email-channel` | A |
| T14 — Cron nhắc học 20:00 | 2 | 2d | `feature/notification/study-reminder-cron` | A |
| T16 — Consumer RabbitMQ | 2 | 2d | `feature/notification/event-consumer` | A |
| — (nền cho T17) | 2 | trong T17 | `feature/notification/reco-readers` | B |
| T17 — Gợi ý rule-based | 2 | 2d | `feature/notification/reco-rule-based-api` | B |
| — (cache) | 2 | trong T17 | `feature/notification/reco-cache` | B |
| T18 — Nâng cấp CF | 3 | 3d | `feature/notification/reco-cf` | B |
| T19 — Test + Swagger | 3 | 1d | `feature/notification/tests-swagger` | A+B |

Quy trình mỗi feature (theo `git-flow-convention.md`): tách nhánh từ `module/notification` → commit theo Conventional Commits → rebase `origin/module/notification` trước khi mở PR → push `--force-with-lease` → PR **squash merge**, 1 approve, CI xanh, ≤ 400 dòng → xoá nhánh feature.

---

## 0.7. Cấu trúc thư mục service

```
services/notification/
├── pyproject.toml
├── Dockerfile
├── .env.example            # chỉ placeholder, KHÔNG có secret thật
└── src/notification/
    ├── main.py             # FastAPI app, mount 2 router, lifespan: scheduler + consumer
    ├── config.py           # pydantic-settings
    ├── db.py               # async engine + session factory
    ├── models.py           # messages, settings, processed_events
    ├── schemas.py          # Pydantic request/response
    ├── deps.py             # TẠM: đọc X-User-Id. TODO: thay bằng pbl6_common khi T02 xong
    ├── errors.py           # TẠM: error envelope. TODO: như trên
    │
    ├── notifications/      # ───── mảng A ─────
    │   ├── router.py
    │   ├── service.py      # create_message(), mark_read()...
    │   ├── cron.py         # APScheduler 20:00
    │   ├── consumer.py     # aio-pika
    │   ├── readers.py      # SELECT read-only: account.users
    │   └── email/
    │       ├── sender.py
    │       └── templates/  # Jinja2
    │
    └── recommendation/     # ───── mảng B ─────
        ├── router.py
        ├── engine.py       # RuleBasedEngine, CFEngine
        ├── readers.py      # SELECT read-only: learning.histories, content.lessons
        ├── cache.py
        └── jobs.py         # (T18) batch CF
```

Hai thư mục con tách bạch, chỉ gặp nhau ở `main.py`, `models.py`, `config.py`, `db.py` — đó là ranh giới cần giữ sạch khi review PR.

---

# A. NotificationService

## A.1. Tổng quan

Quản lý thông báo: in-app, email, và nhắc học hằng ngày. Nhận sự kiện từ service khác qua RabbitMQ và chủ động tạo thông báo theo lịch.

**Làm:** kết nối Supabase + models; API xem/đánh dấu đã đọc/xoá/bật-tắt; cron 20:00; email SMTP/Resend; consumer `payment.succeeded` / `vip.expired` và các event trong contract T04, có retry + DLQ; test + Swagger.

**Không làm:** UI notification center trên web (T56 — Ninthanon, Đạt review PR); push mobile là phần mở rộng (`device_token` đã chừa sẵn).

Ba "cửa vào" độc lập, cùng gọi `notifications/service.py`:

| Cửa vào | Kích hoạt bởi | Việc làm |
|---|---|---|
| HTTP API | Client qua gateway | CRUD message, settings |
| Cron 20:00 | APScheduler | Quét user chưa học → in-app + email |
| Consumer | RabbitMQ event | Dịch event thành message |

---

## A.2. Feature — `feature/notification/service-skeleton` (T12, Sprint 1, 1 ngày)

Phần DDL đã chạy trên Supabase, nên T12 còn lại là **dựng service chạy được và nối vào database**.

### Hướng thực thi

1. `pyproject.toml`: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, pydantic-settings, aio-pika, apscheduler, jinja2, httpx, redis. Quản lý bằng `uv`.
2. `config.py` — pydantic-settings, mọi giá trị từ env:

```
DATABASE_URL          postgresql+asyncpg://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:5432/postgres
DB_SCHEMA             notification
RABBITMQ_URL, REDIS_URL
EMAIL_PROVIDER, EMAIL_API_KEY, EMAIL_FROM
REMINDER_CRON_ENABLED, RECO_PROMOTE_SCORE, RECO_REVIEW_SCORE
```

3. `db.py` — async engine với `search_path` đặt qua `connect_args={"server_settings": {"search_path": "notification,public"}}`. Schema khác luôn gọi bằng tên đầy đủ (`learning.histories`), nên `search_path` không ảnh hưởng.

   **Bẫy thực tế với Supabase:** nếu dùng pooler ở transaction mode, asyncpg phải tắt prepared statement — `connect_args={"statement_cache_size": 0}` — nếu không sẽ gặp `DuplicatePreparedStatementError` ngẫu nhiên. Dùng direct connection (`db.<ref>.supabase.co:5432`) thì không cần, nhưng direct connection chỉ có IPv6 trên plan free.

4. `models.py` — ba bảng ở §0.3, khai báo `__table_args__ = {"schema": "notification"}`. **Không** dùng `create_all()`; schema do file SQL quản lý.
5. `deps.py` tạm: đọc header `X-User-Id` do gateway forward, trả 401 nếu thiếu. Đánh dấu `# TODO: thay bằng pbl6_common.deps khi T02 xong`.
6. `main.py`: app + `GET /health` (sống) + `GET /health/ready` (`select 1` xuống Supabase).
7. Chạy `06_notification_processed_events.sql` trên Supabase.
8. `.env.example` với placeholder. **`.env` thật vào `.gitignore`** — `DATABASE_URL` chứa mật khẩu database, commit là lộ toàn bộ dữ liệu của cả nhóm.

### Definition of Done

`uvicorn` chạy, `GET /health/ready` trả 200 và thực sự query được Supabase; `.env` không nằm trong git.

**Commit mẫu:** `feat(notification): scaffold service with supabase connection and health checks`

---

## A.3. Feature — `feature/notification/notification-api` (T13, Sprint 1, 2 ngày)

### API contract

```
GET    /api/v1/notifications?page=&size=&unread_only=   authenticated
       → { items: [{id, title, content, is_read, created_at}], total, page, size }

PATCH  /api/v1/notifications/{id}/read                  authenticated  → 200
PATCH  /api/v1/notifications/read-all                   authenticated  → { updated: n }
DELETE /api/v1/notifications/{id}                       authenticated  → 204

GET    /api/v1/notifications/settings                   authenticated
       → { enable_daily_reminder, device_token }
PUT    /api/v1/notifications/settings                   authenticated  (upsert)
```

### Hướng thực thi

1. Mọi query filter theo `user_id` từ `deps.py`. Trả **404** khi `id` không thuộc về user hiện tại — không dùng 403, để khỏi lộ sự tồn tại của bản ghi.
2. `GET settings` khi chưa có row → trả defaults (`enable_daily_reminder=true`) và **không** insert; chỉ `PUT` mới upsert (`insert ... on conflict (user_id) do update`). Nhờ vậy account service không phải tạo row lúc đăng ký.
3. Pagination `?page=&size=` → `{items, total, page, size}`. Error envelope thống nhất trong `errors.py`.
4. Viết luôn hàm `create_message(session, user_id, title, content)` trong `service.py` — cron (A.5) và consumer (A.6) chỉ gọi hàm này, không tự viết SQL.

### Definition of Done

Test httpx: list / phân trang / `unread_only`, mark read, read-all, delete, settings upsert, và truy cập message của user khác → 404.

**Commit mẫu:** `feat(notification): add message list/read/delete and settings api`

---

## A.4. Feature — `feature/notification/email-channel` (T15, Sprint 2, 2 ngày)

Làm **trước** cron vì cron cần gửi email.

### Hướng thực thi

1. `EmailSender` protocol, hai implementation: `SmtpSender` (aiosmtplib, dev dùng Mailpit) và `ResendSender` (HTTP). Chọn qua `EMAIL_PROVIDER`.
2. Template Jinja2 **trong code** (`email/templates/`), không phải trong DB — bảng `templates` đã bị bỏ khỏi schema và đó là quyết định đúng.
3. `send_email(user_id, template_name, context)`: đọc `account.users` lấy `email` + `full_name` (read-only, qua `notifications/readers.py`) → render → gửi.
4. Lỗi → retry 3 lần (backoff 1s/5s/25s); vẫn lỗi thì log cảnh báo và **không** làm fail luồng tạo in-app. Email là best-effort, `notification.messages` mới là nguồn sự thật.
5. Template bắt buộc: `study_reminder.html`, `vip_confirmed.html`.

### Definition of Done

Nhận được mail trên Mailpit; unit test mock sender kiểm tra subject + nội dung render.

**Commit mẫu:** `feat(notification): add smtp/resend email sender with jinja templates`

---

## A.5. Feature — `feature/notification/study-reminder-cron` (T14, Sprint 2, 2 ngày, ưu tiên CAO)

### Hướng thực thi

1. APScheduler `AsyncIOScheduler`, `CronTrigger(hour=20, minute=0, timezone="Asia/Ho_Chi_Minh")` — timezone khai báo tường minh, không dựa TZ container.
2. Luồng job (hai query read-only, không JOIN):

```sql
-- 1. user đang hoạt động
select id, email, full_name from account.users
where status = 'ACTIVE' and deleted_at is null;

-- 2. user đã học hôm nay (giờ VN)
select distinct user_id from learning.histories
where completed_at >= :today_start_vn;
```

Lấy hiệu hai tập → loại user có `enable_daily_reminder = false` → mỗi user còn lại: `create_message(...)` + `send_email(...)`.

3. **Idempotency:** trước khi tạo, kiểm tra user đã có message nhắc học trong hôm nay chưa (`title` cố định + `created_at >= today`) → job chạy lại hoặc service restart lúc 20:00 không gửi trùng. Đủ cho một instance; scale ngang cần Redis lock — ghi Known Risks.
4. `REMINDER_CRON_ENABLED=false` để tắt trong test/CI.

### ⚠️ Điểm phải chốt với Hà

`learning.histories` có unique `(user_id, lesson_id)` và cột `highest_score` — tức là **một dòng cho mỗi cặp user–bài**, upsert giữ điểm cao nhất. Câu hỏi: **`completed_at` được cập nhật mỗi lần nộp bài, hay chỉ khi đạt điểm cao hơn?**

Nếu chỉ cập nhật khi điểm cao hơn, user học lại mà điểm thấp hơn sẽ bị tính là "chưa học hôm nay" và nhận nhắc học sai. Đề nghị Hà luôn `set completed_at = now()` ở mọi lần nộp, kể cả khi không cải thiện điểm.

### Definition of Done

Unit test hàm lọc user (fake reader); test chạy job hai lần chỉ ra một message mỗi user; chạy tay thấy cả in-app lẫn email.

**Commit mẫu:** `feat(notification): add 20:00 study reminder cron job`

---

## A.6. Feature — `feature/notification/event-consumer` (T16, Sprint 2, 2 ngày, ưu tiên CAO)

**Không** cần đợi outbox của Long — test bằng cách publish tay vào RabbitMQ.

### Bindings

Queue `notification.events` (durable) bind exchange `pbl6.events`:

| Routing key | Hành động |
|---|---|
| `payment.succeeded` | in-app + email "Kích hoạt VIP thành công" |
| `payment.failed` | in-app "Thanh toán thất bại" |
| `vip.expired` | in-app + email "VIP đã hết hạn" |
| `account.locked` / `account.unlocked` | in-app tương ứng |
| `lesson.published` | in-app "Có bài học mới" |

### Hướng thực thi

1. `consumer.py` chạy trong process FastAPI (khởi động ở lifespan), `aio-pika` robust connection để tự reconnect.
2. **Idempotency:** trong **một transaction** — `INSERT INTO notification.processed_events (event_id, event_type) ...` rồi `create_message(...)`. Trùng `event_id` → đụng primary key → rollback → ack và bỏ qua. Bắt buộc, vì outbox relay là at-least-once.
3. Dispatch theo `event_type` trong envelope. Event type lạ → log rồi ack (quy tắc contract: bỏ qua thứ không biết, **không** nack).
4. **Retry + DLQ:** handler lỗi → nack không requeue; queue khai báo `x-dead-letter-exchange` trỏ `notification.events.dlq`. Đếm header `x-death` để retry 3 lần trước khi rơi hẳn xuống DLQ. Payload sai schema là lỗi không retry được → đẩy thẳng DLQ.

### Definition of Done

Integration test: publish `payment.succeeded` → có message trong DB; publish trùng `event_id` hai lần → chỉ một row; handler lỗi ba lần → message nằm trong DLQ.

**Commit mẫu:** `feat(notification): consume payment and account events with retry + dlq`

---

# B. RecommendationLesson

## B.1. Tổng quan

API `GET /api/v1/lessons/recommended`, hai giai đoạn: rule-based (T17, Sprint 2) chạy realtime và dễ giải thích; collaborative filtering (T18, Sprint 3) là điểm nhấn AI, chạy batch, có fallback về rule-based.

Code tại `services/notification/src/notification/recommendation/`, cùng service và cùng schema với mảng A.

### Dữ liệu đầu vào — đọc read-only, không JOIN

| Cần gì | Nguồn |
|---|---|
| Lịch sử học + điểm | `learning.histories` — `(user_id, lesson_id, highest_score, completed_at)` |
| Bài học ứng viên | `content.lessons` — `(id, category_id, title, level, is_free, status, deleted_at)` |
| Yêu thích (cho CF) | `learning.favorite_lessons` |
| Tier của user | Header `X-User-Tier` từ gateway |

### ⚠️ Ba ràng buộc từ schema thật, đã ảnh hưởng đến thuật toán

1. **`histories` không lưu từng lần làm bài.** Unique `(user_id, lesson_id)` + `highest_score` nghĩa là mỗi cặp user–bài chỉ một dòng, giữ điểm cao nhất. Khái niệm "20 attempts gần nhất" **không tồn tại** — thay bằng "20 bài đã hoàn thành gần nhất" theo `completed_at desc`.
2. **`histories` không có `level`.** Phải lấy `lesson_id` rồi tra `content.lessons` ở query thứ hai, ghép trong Python.
3. **`content.lessons` không có `created_at`.** Không sắp xếp được theo "bài mới publish nhất". Thay bằng **độ phổ biến** — đếm số dòng trong `learning.histories` theo `lesson_id`. Dữ liệu này có thật và ý nghĩa hơn với người học.

**Thang điểm `highest_score`** là `double precision`, schema không ràng buộc khoảng giá trị. Spec này giả định **thang 0–100**; cần Hà xác nhận. Ngưỡng để trong config (`RECO_PROMOTE_SCORE=80`, `RECO_REVIEW_SCORE=50`) nên đổi thang chỉ là đổi env.

---

## B.2. Feature — `feature/notification/reco-readers` (Sprint 2, ~0.5 ngày, trong quota T17)

Toàn bộ SQL cross-schema nằm ở đúng file này. Bốn hàm:

```python
async def fetch_user_history(user_id, limit=20) -> list[HistoryRow]
async def fetch_lessons_by_ids(lesson_ids) -> dict[UUID, LessonRow]
async def fetch_candidate_lessons(levels, only_free: bool) -> list[LessonRow]
async def fetch_lesson_popularity(lesson_ids) -> dict[UUID, int]
```

```sql
-- fetch_user_history
select lesson_id, highest_score, completed_at
from learning.histories
where user_id = :user_id
order by completed_at desc
limit :limit;

-- fetch_candidate_lessons
select id, category_id, title, level, is_free
from content.lessons
where status = 'PUBLISHED' and deleted_at is null
  and level = any(:levels)
  and (:only_free = false or is_free = true);

-- fetch_lesson_popularity
select lesson_id, count(*) as learners
from learning.histories
where lesson_id = any(:lesson_ids)
group by lesson_id;
```

Quy tắc: **chỉ SELECT, không JOIN cross-schema.** Mỗi hàm tương ứng một lời gọi API sau này — khi Hà xong endpoint nội bộ, thay thân hàm, engine không đổi một dòng.

**Commit mẫu:** `feat(recommendation): add read-only cross-schema readers`

---

## B.3. Feature — `feature/notification/reco-rule-based-api` (T17, Sprint 2, 2 ngày)

### API contract

```
GET /api/v1/lessons/recommended?limit=10        authenticated
→ {
    "items": [
      { "lesson_id": "...", "title": "...", "level": "MEDIUM",
        "category_id": "...", "is_free": true,
        "reason": "level_up" }
    ],
    "algo": "rule_based_v1"
  }
```

`reason` ∈ `level_up | practice_same_level | review_lower_level | explore | popular`. Trường này hiển thị được trên FE ("Vì bạn vừa đạt điểm cao ở level EASY…") và là bằng chứng thuật toán khi bảo vệ.

### Thuật toán rule-based v1

Đầu vào: 20 bài hoàn thành gần nhất (`completed_at desc`), đã tra được `level` và `category_id`. `avg(L)` = trung bình `highest_score` các bài ở level `L`.

1. **Level hiện tại:** level cao nhất mà user có ≥ 3 bài đã học và `avg ≥ 50`. Chưa có → `EASY`.
2. **Chọn hướng:**
   - `avg ≥ 80` → **level_up**: bài level kế tiếp (EASY→MEDIUM→HARD; đang HARD thì luyện tiếp HARD).
   - `50 ≤ avg < 80` → **practice_same_level**: bài cùng level chưa học.
   - `avg < 50` → **review_lower_level**: bài level thấp hơn liền kề (EASY thì ở lại EASY).
3. **Lọc ứng viên:** `status='PUBLISHED'`, `deleted_at is null`; user không VIP → chỉ `is_free=true`; loại bài đã có trong `histories` với `highest_score ≥ 80` (đã qua bài).
4. **Xếp hạng:** cùng `category_id` với bài học gần nhất → độ phổ biến giảm dần → còn lại.
5. **Khám phá:** dành 2/10 slot cuối cho bài thuộc category user chưa từng học (`reason=explore`), chống gợi ý một chiều.
6. **Cold start** (chưa có history): bài `EASY` phổ biến nhất, tối đa 2 bài mỗi category, `reason=popular`.
7. **Degrade:** đọc `histories` lỗi → chạy nhánh cold start, vẫn trả 200. Đọc `lessons` lỗi → 503 theo error envelope.

### Definition of Done

Unit test từng nhánh (level_up / same / review / cold start / lọc VIP / loại bài đã qua) với reader giả lập. Test route: user `is_vip=false` không bao giờ nhận bài `is_free=false`.

**Commit mẫu:** `feat(recommendation): add rule-based /lessons/recommended api`

---

## B.4. Feature — `feature/notification/reco-cache` (Sprint 2, ~0.5 ngày)

1. Redis key `reco:{user_id}`, TTL 15 phút.
2. Chấp nhận trễ tối đa 15 phút sau khi user học bài mới — ghi rõ trade-off vào README service. (Invalidate chủ động cần learning publish event `history.updated`, chưa có trong contract T04; đề xuất bổ sung với Đức và Hà nếu thấy cần.)
3. `?refresh=true` bỏ qua cache, dùng khi dev và demo.

**Commit mẫu:** `feat(recommendation): cache recommendations in redis with 15m ttl`

---

## B.5. Feature — `feature/notification/reco-cf` (T18, Sprint 3, 3 ngày, ưu tiên Thấp)

Điểm nhấn AI khi bảo vệ. Làm **sau khi** rule-based chạy ổn; cháy sprint thì cắt được mà không ảnh hưởng luồng chính.

### Chọn item-based Collaborative Filtering

Ma trận user × lesson từ implicit feedback, cosine similarity giữa các lesson. Tính bằng numpy/scipy — không kéo thư viện ML nặng vào image, và giải thích được khi bảo vệ ("học viên giống bạn cũng học bài này").

Trọng số từ dữ liệu có thật:

| Tín hiệu | Nguồn | Trọng số |
|---|---|---|
| Đã học | `learning.histories` | 1 |
| Học tốt (`highest_score ≥ 80`) | `learning.histories` | 2 |
| Yêu thích | `learning.favorite_lessons` | 3 |

Phương án thay thế (content-based embedding với sentence-transformers + pgvector) **không chọn**: `content.lessons.content_url_or_text` có thể chỉ chứa URL chứ không phải nội dung, nên không đảm bảo encode được.

### Hướng thực thi

1. File SQL mới `07_notification_recommendations.sql` — bảng trong schema `notification`:

```sql
create table if not exists notification.lesson_recommendations (
    user_id      uuid not null,
    lesson_id    uuid not null,
    score        double precision not null,
    algo         text not null default 'item_cf_v1',
    generated_at timestamptz not null default now(),
    primary key (user_id, lesson_id)
);
create index on notification.lesson_recommendations (user_id, score desc);
```

2. `jobs.py`: batch APScheduler 02:00 hằng ngày — đọc toàn bộ `histories` + `favorite_lessons` (read-only) → dựng ma trận thưa → tính top 20 lesson mỗi user → upsert.
3. `engine.py`: `CFEngine` đọc bảng precomputed rồi **re-rank** — vẫn áp đủ bộ lọc rule-based (PUBLISHED, `deleted_at is null`, tier, loại bài đã qua). User không có dòng precomputed → fallback nguyên `RuleBasedEngine`. Response trả `algo: "item_cf_v1"`, `reason: "similar_learners"`.
4. Feature flag `RECO_ENGINE=rule_based|cf` — demo được cả hai chế độ khi bảo vệ.
5. Offline check lấy số liệu cho báo cáo: precision@10, train/test split theo `completed_at`.

### Rủi ro dữ liệu

CF cần mật độ tương tác. Seed data của T57 (Ninthanon) là 20 bài + tài khoản demo — quá thưa để CF ra kết quả có nghĩa. **Tự viết script sinh `histories` giả lập** (khoảng 100 user ảo × 5–15 bài, phân bố theo level) trước buổi bảo vệ. Đây là việc phải làm, không phải phương án dự phòng.

**Commit mẫu:** `feat(recommendation): add item-based cf batch job and engine`

---

## B.6. Feature — `feature/notification/tests-swagger` (T19, Sprint 3, 1 ngày)

Áp cho cả hai mảng:

1. Bổ sung coverage các nhánh chưa test, mục tiêu ≥ 80%.
2. Hoàn thiện OpenAPI: tags (`notifications`, `recommendation`), mô tả, ví dụ request/response — để Đức aggregate vào `/docs` (T07).
3. Rà lại error envelope; `GET /health` + `GET /health/ready` (Supabase + RabbitMQ + Redis).
4. Refactor `deps.py` / `errors.py` sang `pbl6_common` nếu T02 của Đức đã xong.

**Commit mẫu:** `test(notification): raise coverage and polish openapi docs`

---

# C. Phụ lục

## C.1. Thứ tự làm & mốc PR lên develop

```
Sprint 1   service-skeleton → notification-api
           └─ PR module/notification → develop   (mốc 1: API thông báo chạy được)

Sprint 2   email-channel → study-reminder-cron
           event-consumer
           reco-readers → reco-rule-based-api → reco-cache
           └─ PR module/notification → develop   (mốc 2: đủ T14/T15/T16/T17)

Sprint 3   reco-cf → tests-swagger
           └─ PR module/notification → develop   (mốc 3: hoàn thiện M2)
```

## C.2. Cần chốt với người khác (không cái nào chặn việc code)

| Với ai | Chốt gì | Nếu chưa có trả lời |
|---|---|---|
| Hà | `histories.completed_at` cập nhật mỗi lần nộp hay chỉ khi điểm cao hơn? (§A.5) | Giả định cập nhật mọi lần; cron có thể sai với user học lại điểm thấp |
| Hà | Thang điểm `highest_score` — 0–100 hay 0–10? | Giả định 0–100, ngưỡng để trong env |
| Đức | Connection string Supabase + cách chia sẻ secret | Tự tạo `.env` local, `.env.example` chỉ placeholder |
| Đức | Schema envelope event trong `pbl6_common` | Tự định nghĩa Pydantic model theo `backend.md` §6, refactor sau |
| Long | Routing key + payload thực tế khi outbox chạy | Publish tay vào RabbitMQ để test |
| Ninthanon | T56 FE notification center có cần `messages.type` không | Nếu cần thì thêm cột bằng `07_*.sql` |

## C.3. Known risks

- **Cross-schema read là nợ kỹ thuật có chủ đích.** Chỉ SELECT, cô lập trong `readers.py`, đổi sang HTTP API khi endpoint của Hà sẵn sàng. Nếu Hà đổi schema mà không báo, recommendation vỡ — cần theo dõi các file `Backend/db/*.sql`.
- Cron chỉ an toàn với **một instance**; scale ngang cần Redis lock. Ngoài phạm vi đồ án.
- Supabase free tier giới hạn connection — mỗi service mở pool riêng trên cùng một database, cần đặt `pool_size` nhỏ (5) và dùng pooler host.
- Email provider free tier có rate limit → cron gửi theo batch có sleep; demo dùng Mailpit.
- CF phụ thuộc mật độ dữ liệu — phải sinh `histories` giả lập trước buổi bảo vệ (§B.5).
- VIP eventual consistency: thông báo có thể đến trước khi account kịp nâng tier — nội dung viết trung tính ("thanh toán thành công, VIP sẽ kích hoạt trong ít phút").
- Cache recommendation trễ 15 phút sau khi user học bài mới — chấp nhận, đã ghi ở B.4.
