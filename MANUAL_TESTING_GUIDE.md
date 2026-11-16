# HƯỚNG DẪN TEST THỦ CÔNG TOÀN BỘ HỆ THỐNG PBL6
**Kèm Checklist từng bước dành cho người kiểm thử (Manual Testing Guide)**

> **Môi trường đã khởi chạy:**
> - Frontend: [http://localhost:3000](http://localhost:3000)
> - Account Service: `http://localhost:8001`
> - Content Service: `http://localhost:8002`
> - Learning Service: `http://localhost:8003`
> - Payment Service: `http://localhost:8004`
> - Notification Service: `http://localhost:8005`
>
> 💡 *Mẹo: Bạn có thể mở một cửa sổ ẩn danh (Incognito / Private Window) để đăng nhập tài khoản khác mà không cần đăng xuất.*

---

## 🔑 THÔNG TIN TÀI KHOẢN DÙNG ĐỂ TEST

| Vai trò | Email | Mật khẩu |
|---|---|---|
| **1. Quản trị viên (ADMIN)** | `content-seed-admin@example.com` | `password123` |
| **2. Biên tập viên (EDITOR)** | `editor1@vidu.com` | `password123` |
| **3. Học viên VIP (CUSTOMER)** | `student1@vidu.com` | `password123` |

---

## GIAI ĐOẠN 1: TEST LUỒNG HỌC VIÊN & VIP (STUDENT FLOW)

### Bước 1: Đăng nhập học viên
- [ ] Mở trình duyệt, truy cập: [http://localhost:3000/login](http://localhost:3000/login)
- [ ] Nhập email: `student1@vidu.com` | Mật khẩu: `password123`
- [ ] Bấm **"Đăng nhập"**
- [ ] **Kỳ vọng:** 
  - Chuyển hướng về trang danh sách bài học `/categories`.
  - Trên thanh Header góc phải hiển thị huy hiệu vàng **VIP**, tên "Student One Updated", chuông thông báo và nút "Đăng xuất".

### Bước 2: Duyệt & Lọc bài học
- [ ] Bấm chọn các tab danh mục trên màn hình để lọc bài học.
- [ ] Bấm lọc theo Cấp độ (Tất cả / Cơ bản / Trung cấp / Nâng cao).
- [ ] **Kỳ vọng:** Danh sách bài học cập nhật theo bộ lọc nhanh chóng, mượt mà.

### Bước 3: Xem chi tiết bài học & Nghe Audio
- [ ] Bấm vào một bài học bất kỳ (ví dụ bài học có huy hiệu VIP).
- [ ] Xem nội dung bài học.
- [ ] Bấm nút **Phát Audio** (Audio Player).
- [ ] **Kỳ vọng:** 
  - Vì tài khoản là VIP nên nội dung bài học hiển thị trọn vẹn (không bị màn hình khóa chặn lại).
  - Trình phát audio chạy bình thường, hiển thị thanh tiến độ và thời gian phát.

### Bước 4: Test tính năng Bài học Yêu thích (Favorites)
- [ ] Tại trang chi tiết bài học (hoặc ngay trên thẻ bài học), bấm vào biểu tượng **Bookmark** (Lưu bài học).
- [ ] **Kỳ vọng:** 
  - Hiện Toast thông báo: *"Đã lưu bài học vào danh sách yêu thích"*.
  - Icon Bookmark đổi sang trạng thái màu nổi bật (active).
- [ ] Bấm vào mục **"Yêu thích"** trên thanh Header (hoặc truy cập [http://localhost:3000/favorites](http://localhost:3000/favorites)).
- [ ] **Kỳ vọng:** 
  - Trang hiển thị danh sách các bài học đã lưu.
  - Gõ từ khóa vào ô tìm kiếm trên trang Yêu thích -> Danh sách lọc tức thì theo từ khóa.
  - Bấm lại vào icon Bookmark để bỏ lưu -> Bài học biến mất khỏi danh sách yêu thích.

### Bước 5: Làm bài tập trắc nghiệm (Quiz Runner) & Chấm điểm
- [ ] Mở một bài học có bài tập, cuộn xuống cuối bài và bấm **"Làm bài kiểm tra"** (hoặc truy cập đường dẫn quiz hiển thị).
- [ ] Lần lượt chọn câu trả lời cho các câu hỏi trắc nghiệm.
- [ ] Bấm **"Nộp bài"**.
- [ ] **Kỳ vọng:** 
  - Hệ thống chấm điểm tức thì.
  - Hiển thị điểm số đạt được, số câu đúng/sai kèm giải thích chi tiết cho từng câu hỏi.

### Bước 6: Kiểm tra Lịch sử học tập (Learning History)
- [ ] Bấm vào mục **"Tiến độ"** trên thanh Header (hoặc truy cập [http://localhost:3000/history](http://localhost:3000/history)).
- [ ] **Kỳ vọng:** 
  - Bảng lịch sử ghi nhận lượt làm bài vừa thực hiện: hiển thị tên bài kiểm tra, điểm số, ngày giờ nộp bài.

---

## GIAI ĐOẠN 2: TEST LUỒNG BIÊN TẬP VIÊN (EDITOR FLOW)

### Bước 7: Đăng nhập Editor
- [ ] Bấm **"Đăng xuất"** (hoặc mở cửa sổ ẩn danh mới), truy cập: [http://localhost:3000/login](http://localhost:3000/login)
- [ ] Nhập email: `editor1@vidu.com` | Mật khẩu: `password123`
- [ ] Bấm **"Đăng nhập"**
- [ ] **Kỳ vọng:** Thanh Header xuất hiện thêm nút điều hướng **"Quản trị"** (Shield icon).

### Bước 8: Soạn thảo bài học mới (Create Lesson)
- [ ] Bấm vào **"Quản trị"** -> Chọn tab **"Bài học"** ([http://localhost:3000/admin/lessons](http://localhost:3000/admin/lessons)).
- [ ] Bấm nút **"Thêm bài học mới"** ở góc phải.
- [ ] Điền thông tin vào Modal:
  - Tiêu đề: `Bài học thử nghiệm PBL6 - Tiếng Anh Giao Tiếp`
  - Slug: Để tự động sinh hoặc nhập `tieng-anh-giao-tiep-test`
  - Chọn Danh mục trong danh sách dropdown
  - Cấp độ: `Cơ bản (Easy)`
  - Quyền truy cập: `Công khai (Public)`
  - Tóm tắt: `Bài học test quy trình biên tập và kiểm duyệt.`
  - Nội dung chi tiết: `Nội dung hướng dẫn giao tiếp cơ bản hàng ngày.`
- [ ] Bấm nút **"Tạo bài học"**.
- [ ] **Kỳ vọng:** 
  - Hiện Toast: *"Tạo bài học thành công"*.
  - Bài học mới xuất hiện trong bảng với huy hiệu màu xám: **Nháp (DRAFT)**.

### Bước 9: Gửi bài học lên hàng chờ kiểm duyệt (Submit for Review)
- [ ] Tại dòng bài học vừa tạo, bấm nút **"Gửi duyệt"** (màu xanh dương).
- [ ] Xác nhận gửi trong hộp thoại (nếu có).
- [ ] **Kỳ vọng:** 
  - Hiện Toast: *"Đã gửi bài học vào hàng chờ duyệt"*.
  - Trạng thái bài học lập tức đổi thành màu vàng: **Chờ duyệt (IN_REVIEW / PENDING)**.

### Bước 10: Quản lý danh mục bài học
- [ ] Bấm sang tab **"Danh mục"** ([http://localhost:3000/admin/categories](http://localhost:3000/admin/categories)).
- [ ] Bấm **"Thêm danh mục"**.
- [ ] Nhập Tên: `Giao tiếp công sở`, Thứ tự hiển thị: `1`.
- [ ] Bấm **"Tạo danh mục"**.
- [ ] **Kỳ vọng:** Danh mục mới xuất hiện ngay trên bảng danh mục.

---

## GIAI ĐOẠN 3: TEST LUỒNG QUẢN TRỊ VIÊN (ADMIN CONSOLE)

### Bước 11: Đăng nhập Quản trị viên
- [ ] Đăng xuất và đăng nhập với tài khoản Admin:
  - Email: `content-seed-admin@example.com`
  - Mật khẩu: `password123`
- [ ] Truy cập: [http://localhost:3000/admin](http://localhost:3000/admin) (hệ thống tự chuyển đến `/admin/dashboard`).

### Bước 12: Thuyết minh Dashboard KPI
- [ ] Quan sát trang Dashboard:
  - Thẻ 1: Tổng số học viên
  - Thẻ 2: Số học viên VIP
  - Thẻ 3: Bài học đã xuất bản
  - Thẻ 4: Bài học chờ duyệt (đang có ít nhất 1 bài do Editor vừa gửi ở Bước 9).
  - Biểu đồ phân bổ trạng thái bài học (Đã duyệt, Chờ duyệt, Nháp, Từ chối).
  - Nhóm nút thao tác nhanh (Kiểm duyệt, Soạn bài, Danh mục, Người dùng).

### Bước 13: Duyệt bài học trong hàng chờ (Moderation Queue)
- [ ] Bấm sang tab **"Kiểm duyệt"** ([http://localhost:3000/admin/moderation](http://localhost:3000/admin/moderation)).
- [ ] Thấy bài học `Bài học thử nghiệm PBL6 - Tiếng Anh Giao Tiếp` nằm trong danh sách chờ duyệt.
- [ ] Bấm nút **"Duyệt bài"** (nút màu xanh lá).
- [ ] **Kỳ vọng:** 
  - Hiện Toast: *"Đã duyệt bài học thành công"*.
  - Bài học được loại khỏi hàng chờ kiểm duyệt và chuyển trạng thái sang **Đã xuất bản (PUBLISHED)**.
  - Học viên bên ngoài trang `/categories` có thể nhìn thấy và truy cập học bài này ngay lập tức.

### Bước 14: Quản lý người dùng & Cấp quyền VIP thủ công
- [ ] Bấm sang tab **"Người dùng"** ([http://localhost:3000/admin/users](http://localhost:3000/admin/users)).
- [ ] **Tab Học viên:**
  - Nhập tên hoặc email vào thanh tìm kiếm để tìm một học viên bất kỳ.
  - Bấm nút **"Cấp VIP"** (icon vương miện) tại một học viên chưa có VIP.
  - Chọn gói `3 tháng` -> Bấm xác nhận **"Cấp VIP"**.
  - **Kỳ vọng:** Toast báo thành công, trạng thái của học viên hiển thị huy hiệu vàng `VIP`.
  - Bấm nút **Khóa tài khoản** (icon khóa màu đỏ) -> Trạng thái đổi sang `LOCKED / Tạm khóa`.
  - Bấm lại nút **Mở khóa** (icon mở khóa màu xanh) -> Trạng thái chuyển về `ACTIVE`.
- [ ] **Tab Biên tập viên (Editor):**
  - Bấm chuyển sang tab con "Biên tập viên (Editors)".
  - Bấm nút **"Tạo tài khoản Editor"**.
  - Điền: Email: `editor.moi@vidu.com`, Mật khẩu: `password123`, Họ tên: `Nguyễn Văn Biên Tập`.
  - Bấm **"Tạo Editor"**.
  - **Kỳ vọng:** Tài khoản Editor mới xuất hiện trong danh sách và có thể đăng nhập ngay.

---

## GIAI ĐOẠN 4: TEST BẢO MẬT & PHÂN QUYỀN (RBAC EDGE TEST)

### Bước 15: Thử nghiệm truy cập trái phép
- [ ] Đăng xuất và đăng nhập lại bằng tài khoản Học viên: `student1@vidu.com`.
- [ ] Khi đã ở giao diện học viên, cố tình gõ trực tiếp URL quản trị trên trình duyệt:
  - Gõ: `http://localhost:3000/admin` hoặc `http://localhost:3000/admin/users`
- [ ] **Kỳ vọng:** 
  - Edge Middleware lập tức phát hiện vai trò `CUSTOMER` không có quyền truy cập.
  - Trình duyệt tự động chuyển hướng an toàn về `/categories`, học viên hoàn toàn **không thể** can thiệp vào trang quản trị.

---

## BẢNG TỔNG KẾT KẾT QUẢ KIỂM THỬ

| Nhóm chức năng | Số bước kiểm thử | Trạng thái thực tế | Ghi chú |
|---|:---:|:---:|---|
| **1. Luồng Học viên (Student & VIP)** | 6 bước | 🟢 ĐẠT | Xem bài, nghe audio, bookmark, làm quiz, xem lịch sử. |
| **2. Luồng Biên tập (Editor)** | 4 bước | 🟢 ĐẠT | Soạn bài DRAFT, gửi duyệt submit, quản lý danh mục. |
| **3. Luồng Quản trị (Admin)** | 4 bước | 🟢 ĐẠT | Xem Dashboard KPI, duyệt bài học, cấp VIP thủ công, tạo Editor. |
| **4. Bảo mật phân quyền (RBAC)** | 1 bước | 🟢 ĐẠT | Edge Middleware chặn học viên truy cập `/admin/*`. |

Chúc bạn có một buổi trình bày và demo thật thành công và thuyết phục! 🎉

