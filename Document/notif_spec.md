# Đặc tả chức năng Quản lý thông báo (Mục 8)

**Service:** `notification` — port `8005` — schema `notification` trên Supabase
**Owner:** Đạt · Backend: **FastAPI** (Python 3.12)
**Tài liệu liên quan:** `Document/project_spec_M2_notification_recommendation.md` (kế hoạch module, git flow), `Backend/db/*.sql` (DDL), `Backend/backend.md` (kiến trúc, event contract)

---

## 1. Phạm vi

| Mã | Chức năng | Thực hiện bởi | Task |
|---|---|---|---|
| 8.1 | Tự động gửi **email** nhắc nhở học bài mỗi ngày | Cron 20:00 + email sender | T14, T15 |
| 8.2 | Gửi **thông báo in-app** qua tài khoản website | API nội bộ + RabbitMQ consumer | T13, T16 |
| 8.3 | Customer **xem** thông báo | `GET /notifications` | T13 |
| 8.4 | Customer **xoá** thông báo | `DELETE /notifications/{id}` | T13 |
| 8.5 | Customer **bật/tắt** nhận thông báo | `GET`/`PUT /notifications/settings` | T13 |

Ba chức năng 8.3–8.5 là API đồng bộ do Customer gọi. Hai chức năng 8.1–8.2 là luồng chủ động của hệ thống, Customer không kích hoạt.

**Không thuộc phạm vi tài liệu này:** gợi ý bài học (`/lessons/recommended`), UI notification center trên web (T56 — Ninthanon làm, Đạt review PR), push notification mobile (cột `settings.device_token` đã chừa sẵn nhưng chưa dùng).

---

## 2. Công nghệ sử dụng

### 2.1. Đã cài và đang chạy (T12 hoàn thành)

| Thành phần | Công nghệ | Vì sao chọn |
|---|---|---|
| Web framework | **FastAPI 0.115+** | Tự sinh OpenAPI cho gateway gộp (T07); async native nên một process xử lý được nhiều request I/O-bound; validate request bằng Pydantic không phải viết tay |
| ASGI server | **Uvicorn** | Dev dùng `--reload`; production chạy trong container |
| ORM | **SQLAlchemy 2.0 async** | Kiểu `Mapped[...]` cho IDE gợi ý được; async khớp với FastAPI |
| Driver DB | **asyncpg** | Driver async nhanh nhất cho PostgreSQL |
| Database | **Supabase PostgreSQL** | Shared DB, service sở hữu schema `notification` |
| Cấu hình | **pydantic-settings** | Mọi giá trị từ biến môi trường, không hardcode secret |
| Validate | **Pydantic v2** | Dùng chung cho request/response và payload event |
| Test | **pytest + pytest-asyncio + httpx** | `ASGITransport` test endpoint không cần chạy server thật |
| Lint/format | **ruff** | Thay cả flake8 + isort + black, chạy nhanh trong CI |
| Đóng gói | **uv + Docker multi-stage** | `uv.lock` đảm bảo container cài đúng phiên bản như máy dev |

### 2.2. Cần thêm theo từng chức năng

| Chức năng | Công nghệ | Thêm vào | Ghi chú |
|---|---|---|---|
| 8.1 — hẹn giờ | **APScheduler** (`AsyncIOScheduler`) | nhóm `scheduling` | Chạy trong process FastAPI, không cần cron hệ thống |
| 8.1 — timezone | **tzdata** | dependency chính | **Bắt buộc trên Windows** — `zoneinfo` của Python không có sẵn dữ liệu múi giờ trên Windows, thiếu package này thì `ZoneInfo("Asia/Ho_Chi_Minh")` ném `ZoneInfoNotFoundError` |
| 8.1 — gửi email | **aiosmtplib** | nhóm `email` | Client SMTP async, không chặn event loop |
| 8.1 — nội dung email | **Jinja2** | nhóm `email` | Template HTML để trong code, version control được |
| 8.1 — test email | **Mailpit** (Docker) | docker-compose | SMTP server giả cho dev, có UI xem mail tại `localhost:8025`, không gửi ra ngoài thật |
| 8.2 — nhận event | **aio-pika** | nhóm `messaging` | Client RabbitMQ async, hỗ trợ robust connection tự reconnect |
| 8.2 — message broker | **RabbitMQ** | docker-compose | Exchange `pbl6.events` dạng topic, có DLQ |

Cài bằng:

```bash
uv add tzdata
uv add --optional scheduling apscheduler
uv add --optional email aiosmtplib jinja2
uv add --optional messaging aio-pika
```

### 2.3. Nhà cung cấp email — cần chốt

| Phương án | Ưu | Nhược | Khuyến nghị |
|---|---|---|---|
| **Gmail SMTP** | Miễn phí, chỉ cần App Password | Giới hạn ~500 mail/ngày, dễ bị đánh dấu spam | ✅ Đủ cho demo đồ án |
| **Resend** | API sạch, 3000 mail/tháng free | Phải verify domain mới gửi được cho người khác; chưa verify thì chỉ gửi được tới email đã đăng ký | Dùng nếu nhóm có domain |
| **Mailpit** | Không gửi ra ngoài, xem được ngay | Chỉ dùng được ở local | ✅ Bắt buộc cho dev/test |

Kiến trúc code tách `EmailSender` thành protocol nên đổi nhà cung cấp chỉ là đổi biến môi trường `EMAIL_PROVIDER`, không sửa logic.

---

## 3. Dữ liệu

Schema do **Alembic** quản lý, mỗi service một lịch sử migration riêng — giống account và content. Các file trong `Backend/db/` chỉ là **baseline** ghi lại những gì đã tạo tay trên Supabase trước khi Alembic được dựng.

| Revision | Bảng | Cách áp |
|---|---|---|
| `0001` | `messages`, `settings` — mirror `05_notification.sql` | `alembic stamp 0001` (Supabase đã có sẵn) |
| `0002` | `processed_events` | `alembic upgrade head` |

Mỗi service giữ bảng `alembic_version` **bên trong schema của chính nó** (`version_table_schema` trong `alembic/env.py`), nên năm service dùng chung một database Supabase không đụng nhau.

```sql
notification.messages              -- thông báo in-app (8.2, 8.3, 8.4)
  id         uuid pk
  user_id    uuid not null         -- logical FK -> account.users.id
  title      text not null
  content    text not null
  is_read    boolean not null default false
  created_at timestamptz not null default now()

notification.settings              -- tuỳ chọn người dùng (8.5)
  user_id               uuid pk
  enable_daily_reminder boolean not null default true
  device_token          text

notification.processed_events      -- chống xử lý trùng event (8.2)
  event_id     uuid pk
  event_type   text not null
  processed_at timestamptz not null default now()
```

Model SQLAlchemy tương ứng đã có tại `src/notification/models.py`: `Message`, `NotificationSetting`, `ProcessedEvent`.

### Hai giới hạn của schema và cách xử lý

**Không có `messages.type`.** FE không phân loại được thông báo để chọn icon hoặc điều hướng khi bấm vào. Hiện chấp nhận — `title` đủ mô tả. Nếu T56 cần, thêm cột bằng file `07_*.sql`.

**Không có `deleted_at` trên `messages`.** Nên 8.4 là **xoá vật lý** (`DELETE`), không phải soft delete. Chấp nhận được: thông báo không phải dữ liệu cần audit, và user đã chủ động xoá thì không cần giữ lại.

---

## 4. Kiến trúc: ba cửa vào, một lớp nghiệp vụ

```
┌─ Customer (qua gateway) ─┐
│  GET    /notifications   │  8.3
│  DELETE /notifications   │  8.4   ──┐
│  PUT    /settings        │  8.5     │
└──────────────────────────┘          │
                                      ├──► service.py ──► notification.messages
┌─ APScheduler 20:00 ──────┐          │    (nghiệp vụ         (Supabase)
│  quét user chưa học      │  8.1   ──┤     dùng chung)
│  → in-app + email        │          │
└──────────────────────────┘          │
                                      │
┌─ RabbitMQ consumer ──────┐          │
│  payment.succeeded...    │  8.2   ──┘
└──────────────────────────┘
```

Cả ba cửa vào đều gọi **cùng một hàm** `create_message()` trong `notifications/service.py`. Không cửa nào tự viết SQL insert — nếu sau này cần ghi log mỗi lần tạo thông báo thì chỉ sửa một chỗ.

### Cấu trúc file

```
src/notification/
├── main.py                      đã có — app, health, mount router
├── config.py                    đã có — cần thêm biến email/cron
├── db.py                        đã có
├── models.py                    đã có — 3 bảng
├── deps.py                      đã có — X-User-Id → CurrentUser
├── errors.py                    đã có — error envelope
├── schemas.py                   ← 8.3/8.4/8.5: Pydantic request/response
└── notifications/
    ├── router.py                ← 8.3, 8.4, 8.5
    ├── service.py               ← create_message(), mark_read(), delete()
    ├── readers.py               ← 8.1: SELECT account.users (read-only)
    ├── cron.py                  ← 8.1: APScheduler job
    ├── consumer.py              ← 8.2: aio-pika
    ├── events.py                ← 8.2: Pydantic model cho envelope + payload
    └── email/
        ├── sender.py            ← 8.1: SmtpSender / ResendSender
        └── templates/
            ├── base.html
            ├── study_reminder.html
            └── vip_confirmed.html
```

---

## 5. Chức năng 8.1 — Nhắc nhở học bài qua email hằng ngày

> *Hệ thống tự động gửi email nhắc nhở người dùng học bài mỗi ngày.*

### 5.1. Luồng xử lý

```
20:00 (giờ VN) — APScheduler kích hoạt
    │
    ├─ 1. Lấy user đang hoạt động          SELECT account.users WHERE status='ACTIVE'
    ├─ 2. Lấy user đã học hôm nay          SELECT learning.histories WHERE completed_at >= today
    ├─ 3. Hiệu hai tập → user chưa học hôm nay
    ├─ 4. Loại user có enable_daily_reminder = false        (8.5)
    ├─ 5. Loại user đã nhận nhắc học hôm nay               (chống gửi trùng)
    │
    └─ Với mỗi user còn lại:
          ├─ create_message(...)      → thông báo in-app
          └─ send_email(...)          → email nhắc học
```

### 5.2. Hai câu SQL (không JOIN cross-schema)

```sql
-- Bước 1
SELECT id, email, full_name
FROM account.users
WHERE status = 'ACTIVE' AND deleted_at IS NULL;

-- Bước 2
SELECT DISTINCT user_id
FROM learning.histories
WHERE completed_at >= :today_start_vn;
```

Hai query riêng rồi ghép trong Python — giữ nguyên tắc bounded context, và mỗi query tương ứng một lời gọi API sau này khi Hà/Long làm xong endpoint nội bộ (xem project_spec §0.4).

### 5.3. Cấu hình APScheduler

```python
scheduler = AsyncIOScheduler()
scheduler.add_job(
    send_daily_reminders,
    CronTrigger(hour=settings.reminder_hour, minute=0,
                timezone=ZoneInfo(settings.reminder_timezone)),
    id="daily_study_reminder",
    max_instances=1,        # job trước chưa xong thì không chạy job mới
    coalesce=True,          # bỏ lần chạy bị trễ, không dồn lại chạy liên tiếp
)
```

Timezone khai báo tường minh `Asia/Ho_Chi_Minh`, **không** dựa vào TZ của container — container mặc định UTC, nếu không khai báo thì job chạy lúc 03:00 sáng giờ VN.

Scheduler khởi động trong `lifespan` của FastAPI, tắt được bằng `REMINDER_CRON_ENABLED=false` cho test và CI.

### 5.4. Chống gửi trùng

Trước khi tạo, kiểm tra user đã có thông báo nhắc học trong hôm nay chưa:

```sql
SELECT 1 FROM notification.messages
WHERE user_id = :uid
  AND title = :reminder_title
  AND created_at >= :today_start_vn
LIMIT 1;
```

Cần thiết vì: service restart đúng 20:00, hoặc job bị gọi lại thủ công, hoặc deploy lại giữa lúc job đang chạy. Không có kiểm tra này thì user nhận hai email giống nhau.

*Giới hạn:* chỉ an toàn khi chạy **một instance**. Nhiều instance thì cả hai cùng kiểm tra thấy "chưa có" rồi cùng gửi — cần Redis lock, ngoài phạm vi đồ án.

### 5.5. Gửi email

```python
async def send_email(user_email: str, template: str, context: dict) -> bool:
    """Trả về False khi gửi thất bại — KHÔNG raise."""
```

Ba nguyên tắc:

1. **Email là best-effort.** Gửi lỗi thì log cảnh báo, không làm fail việc tạo thông báo in-app. `notification.messages` là nguồn sự thật, email chỉ là kênh phụ.
2. **Retry 3 lần** với backoff 1s / 5s / 25s. Lỗi SMTP thường là tạm thời.
3. **Gửi theo batch có nghỉ.** Gmail giới hạn ~500 mail/ngày và chặn nếu gửi quá nhanh — gửi từng lô 50 mail rồi `asyncio.sleep(1)`.

Template `study_reminder.html` dùng biến: `full_name`, `app_url`. Nội dung ngắn, có một nút dẫn về trang danh sách bài học.

### 5.6. Definition of Done

- Unit test hàm lọc user (mock hai reader) phủ các nhánh: user đã học hôm nay, user tắt nhắc nhở, user đã nhận nhắc hôm nay.
- Chạy job hai lần liên tiếp chỉ tạo một thông báo mỗi user.
- Email hiện trên Mailpit UI với nội dung render đúng tên người nhận.
- Job chạy đúng 20:00 giờ VN khi container ở UTC.

### 5.7. ⚠️ Cần chốt với Hà

`learning.histories` có `UNIQUE (user_id, lesson_id)` và cột `highest_score` — một dòng cho mỗi cặp user–bài, upsert giữ điểm cao nhất. Câu hỏi: **`completed_at` được cập nhật mỗi lần nộp bài, hay chỉ khi đạt điểm cao hơn?**

Nếu chỉ cập nhật khi điểm cao hơn, user học lại mà điểm thấp hơn sẽ bị tính là "chưa học hôm nay" và nhận email nhắc học sai. Đề nghị Hà luôn `SET completed_at = now()` ở mọi lần nộp bài.

---

## 6. Chức năng 8.2 — Gửi thông báo in-app

> *Hệ thống gửi thông báo qua tài khoản website của người dùng.*

### 6.1. Ai tạo thông báo in-app

Ba nguồn, không có nguồn nào do Customer trực tiếp gọi:

| Nguồn | Khi nào | Tiêu đề |
|---|---|---|
| Cron 20:00 | Mỗi ngày (8.1) | "Đã đến giờ học hôm nay" |
| Consumer `payment.succeeded` | Thanh toán thành công | "Thanh toán thành công" |
| Consumer `payment.failed` | Thanh toán thất bại | "Thanh toán không thành công" |
| Consumer `vip.expired` | VIP hết hạn | "Gói VIP đã hết hạn" |
| Consumer `account.locked` | Admin khoá tài khoản | "Tài khoản đã bị khoá" |
| Consumer `account.unlocked` | Admin mở khoá | "Tài khoản đã được mở khoá" |
| Consumer `lesson.published` | Có bài học mới | "Có bài học mới" |

### 6.2. Hàm nghiệp vụ dùng chung

```python
async def create_message(
    session: AsyncSession, user_id: UUID, title: str, content: str
) -> Message:
    """Tạo một thông báo in-app. Mọi nguồn đều đi qua đây."""
```

### 6.3. Consumer RabbitMQ

Queue `notification.events` (durable) bind vào exchange `pbl6.events` với các routing key ở bảng trên.

**Idempotency — bắt buộc.** Trong **một transaction duy nhất**:

```python
async with session.begin():
    session.add(ProcessedEvent(event_id=envelope.event_id, event_type=envelope.event_type))
    await create_message(session, ...)
    # trùng event_id → IntegrityError → rollback cả hai → ack và bỏ qua
```

Vì sao cần: outbox relay của payment là **at-least-once**. Crash giữa lúc publish và lúc đánh dấu đã publish sẽ khiến event được gửi lại. Không có bảng dedupe thì user nhận hai thông báo "Thanh toán thành công" cho cùng một giao dịch.

Vì sao phải **cùng** transaction: tách ra thì hoặc đánh dấu đã xử lý mà chưa tạo thông báo (user không bao giờ nhận được), hoặc tạo thông báo rồi mới đánh dấu (crash ở giữa → tạo lần hai).

**Retry + DLQ:**

```
handler lỗi → nack(requeue=False) → x-dead-letter-exchange
   → đếm header x-death, retry 3 lần → rơi hẳn vào notification.events.dlq
```

Payload sai schema là lỗi **không retry được** (retry bao nhiêu lần cũng sai) → đẩy thẳng DLQ. Event type lạ → log rồi **ack** (quy tắc contract: consumer bỏ qua thứ không hiểu, không nack).

**Thứ tự quan trọng:** commit transaction trước, gửi email sau. Email không nằm trong transaction được vì nó gửi ra ngoài hệ thống; đặt sau commit để in-app luôn chính xác.

### 6.4. Envelope event

```python
class EventEnvelope(BaseModel):
    event_id: UUID
    event_type: str
    version: int
    occurred_at: datetime
    producer: str
    data: dict
```

Viết trong `notifications/events.py`, đánh dấu `TODO(T04)` để sau thay bằng `pbl6_common.events.schemas` của Đức.

### 6.5. ⚠️ Cần chốt với Long

**`event_id` được sinh lúc nào?** Phải sinh khi `INSERT` vào bảng `outbox`, **không** phải lúc relay publish. Nếu sinh mới mỗi lần publish thì bảng `processed_events` vô dụng — mỗi lần giao lại có id khác nhau nên không so trùng được, và user vẫn nhận thông báo hai lần dù code phía notification đúng hoàn toàn.

### 6.6. Definition of Done

- Publish `payment.succeeded` → có đúng một dòng trong `messages`.
- Publish trùng `event_id` hai lần → vẫn chỉ một dòng.
- Handler ném lỗi ba lần → message nằm trong DLQ, service vẫn chạy.
- Event type lạ → được ack, không vào DLQ, không crash.

---

## 7. Chức năng 8.3 — Xem thông báo

> *Hệ thống cho phép Customer xem các thông báo được gửi từ hệ thống.*

### 7.1. API

```http
GET /api/v1/notifications?page=1&size=20&unread_only=false
Authorization: Bearer <JWT>        (gateway verify, forward X-User-Id)
```

```json
{
  "items": [
    {
      "id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
      "title": "Đã đến giờ học hôm nay",
      "content": "Bạn chưa hoàn thành bài học nào hôm nay...",
      "is_read": false,
      "created_at": "2026-10-09T13:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "size": 20,
  "unread_count": 7
}
```

Kèm hai endpoint đánh dấu đã đọc — `is_read` đã có trong schema nên phải có API để đổi nó:

```http
PATCH /api/v1/notifications/{id}/read     → 204 No Content
PATCH /api/v1/notifications/read-all      → 200 { "updated": 7 }
```

### 7.2. Hướng thực thi

1. `user_id` lấy từ `CurrentUserDep` (`deps.py`, đọc header `X-User-Id` gateway forward). **Mọi query đều filter theo `user_id`** — không có ngoại lệ.
2. Sắp xếp `created_at DESC` — thông báo mới nhất lên đầu.
3. `unread_only=true` thêm điều kiện `is_read = false`, dùng đúng index `messages_user_unread_idx` đã có trong schema.
4. `unread_count` tính bằng một query `COUNT` riêng — FE cần số này để hiện badge, nếu không trả thì FE phải gọi thêm một lần nữa.
5. `size` giới hạn tối đa 100 (`Query(default=20, le=100)`) — chặn client xin 10000 dòng một lượt.

### 7.3. Definition of Done

- Phân trang đúng: `total` là tổng toàn bộ, không phải số dòng của trang hiện tại.
- `unread_only=true` chỉ trả thông báo chưa đọc.
- Thông báo của user khác **không bao giờ** xuất hiện.
- `size=500` → bị từ chối 422.

---

## 8. Chức năng 8.4 — Xoá thông báo

> *Hệ thống cho phép Customer xoá các thông báo được gửi từ hệ thống.*

### 8.1. API

```http
DELETE /api/v1/notifications/{id}          → 204 No Content
```

### 8.2. Hướng thực thi

1. Xoá vật lý (`DELETE`), vì `messages` không có cột `deleted_at`.
2. Query xoá **luôn kèm `user_id`** trong điều kiện:

```sql
DELETE FROM notification.messages
WHERE id = :id AND user_id = :current_user_id;
```

Viết như vậy thì ngay cả khi logic kiểm tra phía trên có lỗi, câu SQL cũng không thể xoá thông báo của người khác.

3. `rowcount = 0` → trả **404**, không phải 403. Lý do: trả 403 vô tình tiết lộ rằng id đó tồn tại và thuộc về người khác. 404 không cho kẻ tấn công biết gì.
4. Xoá hai lần cùng một id → lần thứ hai trả 404. Chấp nhận được; nếu muốn idempotent hoàn toàn thì trả 204 cả hai lần, nhưng khi đó không phân biệt được "đã xoá" với "không phải của bạn".

### 8.3. Definition of Done

- Xoá thông báo của chính mình → 204, dòng mất khỏi DB.
- Xoá thông báo của user khác → 404, dòng **vẫn còn** trong DB.
- Xoá id không tồn tại → 404.

---

## 9. Chức năng 8.5 — Bật/tắt nhận thông báo

> *Hệ thống cho phép Customer bật/tắt tính năng thông báo của hệ thống.*

### 9.1. Phạm vi của công tắc — cần hiểu đúng

Schema chỉ có một cờ `enable_daily_reminder`. Câu hỏi: tắt nó thì tắt những gì?

| Loại thông báo | Ví dụ | Cho tắt? |
|---|---|---|
| **Nhắc nhở định kỳ** | Nhắc học 20:00 hằng ngày | ✅ Có — đây là mục đích của cờ |
| **Thông báo giao dịch** | Thanh toán thành công, VIP hết hạn, tài khoản bị khoá | ❌ Không |

Lý do không cho tắt nhóm thứ hai: đó là thông tin người dùng **cần biết** về tài khoản và tiền của họ. Một người tắt thông báo rồi không biết mình đã bị trừ tiền hay tài khoản bị khoá là trải nghiệm tệ, và các hệ thống thực tế đều phân biệt hai nhóm này.

Vậy `enable_daily_reminder = false` nghĩa là: **không nhận nhắc học, cả in-app lẫn email**. Thông báo giao dịch vẫn gửi bình thường.

Một cờ là đủ cho 8.5. Nếu sau này muốn tách riêng "tắt email nhưng giữ in-app" thì thêm cột `email_enabled` bằng file `07_*.sql`.

### 9.2. API

```http
GET /api/v1/notifications/settings
→ { "enable_daily_reminder": true, "device_token": null }

PUT /api/v1/notifications/settings
   { "enable_daily_reminder": false }
→ { "enable_daily_reminder": false, "device_token": null }
```

### 9.3. Hướng thực thi

1. **`GET` khi chưa có row → trả mặc định, KHÔNG insert.** Chỉ `PUT` mới ghi. Nhờ vậy account service không phải tạo row lúc user đăng ký, và bảng `settings` chỉ chứa những user thực sự đã thay đổi tuỳ chọn.

2. `PUT` dùng upsert một câu, không `SELECT` rồi `INSERT`:

```python
stmt = insert(NotificationSetting).values(
    user_id=user.id, enable_daily_reminder=payload.enable_daily_reminder
).on_conflict_do_update(
    index_elements=["user_id"],
    set_={"enable_daily_reminder": payload.enable_daily_reminder},
)
```

Viết tách thành `SELECT` rồi `INSERT` sẽ có race condition: hai request đồng thời đều thấy "chưa có row" rồi cùng `INSERT`, request thứ hai vỡ vì trùng primary key.

3. Cron (8.1) đọc cờ này ở bước 4 của luồng. Mặc định `true` — user mới sẽ nhận nhắc học, phải chủ động tắt.

### 9.4. Definition of Done

- `GET` lần đầu (chưa có row) → trả `enable_daily_reminder: true`, bảng vẫn trống.
- `PUT false` rồi `GET` → trả `false`.
- `PUT` hai lần liên tiếp → không lỗi trùng key.
- Tắt rồi chạy cron → user **không** nhận nhắc học.
- Tắt rồi publish `payment.succeeded` → user **vẫn** nhận thông báo thanh toán.

---

## 10. Bảo mật

### 10.1. Xác thực — service không đọc JWT

Gateway verify JWT rồi forward `X-User-Id`, `X-User-Roles`, `X-User-Tier`. Service chỉ đọc header (`deps.py`).

**Rủi ro phải phòng:** nếu ai gọi trực tiếp được vào port 8005, họ chỉ cần gửi `X-User-Id: <uuid bất kỳ>` là đọc và xoá được thông báo của người khác — không cần mật khẩu.

Bắt buộc: trong `docker-compose.yml` **không map port ra host** cho service này. Dùng `expose: 8005` để container khác gọi được, tuyệt đối không `ports: "8005:8005"`. Trên VPS phải chặn cổng ở firewall. Đây là việc của Đức (T03) nhưng cần nhắc, vì sai thì mất bảo mật mà không có dấu hiệu gì.

Nên đề xuất thêm với Đức: gateway gắn `X-Internal-Token: <secret dùng chung>`, service từ chối request thiếu header này. Khi đó dù port có lộ, kẻ tấn công vẫn không vào được.

### 10.2. Phân quyền dữ liệu

Mọi endpoint 8.3/8.4/8.5 đều **chỉ** chạm dữ liệu của chính user gọi. Không có endpoint nào cho user xem thông báo của người khác, kể cả ADMIN — nếu sau này cần cho Admin, phải là endpoint riêng có kiểm tra role.

### 10.3. Secret

`DATABASE_URL` chứa mật khẩu Supabase và cho quyền truy cập **toàn bộ** schema của cả nhóm, không riêng `notification`. Nó nằm trong `.env`, đã được `.gitignore` chặn. `EMAIL_API_KEY` và App Password của Gmail cũng vậy. `.env.example` chỉ chứa placeholder.

---

## 11. Kiểm thử

| Loại | Công cụ | Phạm vi |
|---|---|---|
| Unit | pytest | Hàm lọc user của cron, logic chọn template, parse envelope event |
| API | httpx `ASGITransport` | 6 endpoint của 8.3/8.4/8.5, gồm cả case truy cập dữ liệu người khác |
| Integration | RabbitMQ thật (Docker) | Publish event → kiểm tra `messages`; publish trùng → chỉ 1 dòng; lỗi 3 lần → DLQ |
| Email | Mailpit | Nội dung render, đúng người nhận |

Mục tiêu coverage ≥ 80% (quality gate `backend.md` §9).

**Ba test quan trọng nhất** — nếu chỉ viết được ba thì viết ba cái này:

1. Truy cập thông báo của user khác → 404 (bảo mật).
2. Publish trùng `event_id` → chỉ một thông báo (idempotency).
3. Chạy cron hai lần → chỉ một email mỗi user (chống gửi trùng).

---

## 12. Thứ tự thực hiện

```
Sprint 1   T13 — API 8.3, 8.4, 8.5
           feature/notification/notification-api
           → thi công được ngay, không phụ thuộc ai

Sprint 2   T15 — email sender (8.1 phần gửi)
           feature/notification/email-channel

           T14 — cron 20:00 (8.1 phần hẹn giờ)
           feature/notification/study-reminder-cron
           → cần contract last-activity với Hà, mock được nếu chưa có

           T16 — consumer (8.2)
           feature/notification/event-consumer
           → test bằng publish tay, không chờ outbox của Long

Sprint 3   T19 — hoàn thiện test + Swagger
           feature/notification/tests-swagger
```

Làm 8.3/8.4/8.5 trước vì chúng độc lập hoàn toàn và tạo ra hàm `create_message()` mà 8.1 với 8.2 đều cần.

Trong 8.1 làm email sender trước cron, vì cron gọi email.

---

## 13. Tổng hợp những điểm cần chốt

| Với ai | Chốt gì | Nếu chưa có trả lời |
|---|---|---|
| Hà | `histories.completed_at` cập nhật mỗi lần nộp hay chỉ khi điểm cao hơn? (§5.7) | Giả định cập nhật mọi lần; cron có thể nhắc sai với user học lại điểm thấp |
| Long | `event_id` sinh lúc INSERT outbox hay lúc publish? (§6.5) | Giả định lúc INSERT; nếu sai thì chống trùng không hoạt động |
| Đức | Có port-map service ra host không? Có `X-Internal-Token` không? (§10.1) | Giả định không map port — phải kiểm tra lại khi có docker-compose |
| Đức | T04 có code Pydantic cho event không, hay mỗi người tự viết? | Tự viết trong `events.py`, đánh dấu TODO, gộp sau |
| Nhóm | Dùng Gmail SMTP hay Resend? (§2.3) | Mailpit cho dev, quyết định trước Sprint 2 |
| Ninthanon | T56 có cần `messages.type` để phân loại icon không? | Nếu cần thì thêm cột bằng `07_*.sql` |
