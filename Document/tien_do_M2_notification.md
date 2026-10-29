# Báo cáo tiến độ — Module M2: Thông báo & Gợi ý bài học

**Người thực hiện:** Đạt
**Phạm vi:** Notification Service (chức năng 8.1–8.5) và Recommendation Lesson
**Cập nhật:** 15/10/2026

---

## 1. Tóm tắt

Module M2 phụ trách hai mảng: **gửi và quản lý thông báo** cho người học, và **gợi ý bài học** phù hợp với trình độ từng người. Cả hai nằm trong một service duy nhất tên `notification`.

Tính đến nay đã hoàn thành **3/8 đầu việc** theo bảng phân công, tương đương 5/15 ngày công. Ba chức năng người dùng cuối nhìn thấy được đã chạy: xem thông báo, xoá thông báo, bật/tắt nhận thông báo. Phần gửi email cũng đã hoạt động, đang chờ ghép với bộ hẹn giờ.

| Nhóm chức năng | Trạng thái |
|---|---|
| Xem / xoá / bật tắt thông báo | ✅ Hoàn thành |
| Gửi email | ✅ Hoàn thành |
| Nhắc học tự động 20:00 | ⬜ Đang chờ làm |
| Nhận thông báo từ service khác | ⬜ Đang chờ làm |
| Gợi ý bài học | ⬜ Sprint 3 |

---

## 2. Các chức năng đã hoàn thành

### 2.1. Xem thông báo (chức năng 8.3)

Người học mở mục Thông báo sẽ thấy danh sách tất cả thông báo hệ thống gửi cho mình, **mới nhất ở trên cùng**.

Những gì đã làm được:

- **Chỉ thấy thông báo của chính mình.** Không có cách nào để một người xem thông báo của người khác, kể cả khi họ biết mã số của thông báo đó.
- **Chia trang.** Mặc định 20 thông báo mỗi trang, người dùng chuyển trang để xem tiếp. Có giới hạn tối đa 100 mỗi lần để không ai tải nặng hệ thống.
- **Lọc chưa đọc.** Có thể chọn chỉ xem những thông báo chưa đọc.
- **Đếm số chưa đọc.** Hệ thống luôn trả về con số này để giao diện hiển thị dấu chấm đỏ trên chuông thông báo.
- **Đánh dấu đã đọc** từng cái một, hoặc đánh dấu tất cả cùng lúc.

Một chi tiết nhỏ nhưng quan trọng: khi hệ thống gửi hàng loạt thông báo cùng lúc (ví dụ nhắc học cho 1000 người), chúng được tạo trong cùng một khoảnh khắc. Nếu sắp xếp chỉ theo thời gian, cùng một thông báo có thể xuất hiện ở cả trang 1 lẫn trang 2. Chúng tôi đã xử lý để điều này không xảy ra.

### 2.2. Xoá thông báo (chức năng 8.4)

Người học có thể xoá thông báo không còn cần thiết.

- Chỉ xoá được thông báo của chính mình.
- Nếu cố xoá thông báo của người khác, hệ thống trả về "không tìm thấy" thay vì "không có quyền". Lý do: câu trả lời "không có quyền" vô tình tiết lộ rằng thông báo đó có tồn tại và thuộc về ai đó — thông tin mà người lạ không nên biết.
- Thông báo bị xoá vĩnh viễn, không lưu lại. Đây là dữ liệu người dùng chủ động bỏ đi, không phải hồ sơ cần đối chiếu sau này.

### 2.3. Bật / tắt nhận thông báo (chức năng 8.5)

Người học tự quyết định có muốn nhận nhắc nhở hằng ngày hay không.

Điểm cần giải thích rõ: **công tắc này chỉ tắt nhắc nhở học bài**, không tắt các thông báo quan trọng về tài khoản.

| Loại thông báo | Ví dụ | Tắt được? |
|---|---|---|
| Nhắc nhở định kỳ | Nhắc học lúc 20:00 | ✅ Có |
| Thông báo giao dịch | Thanh toán thành công, VIP hết hạn, tài khoản bị khoá | ❌ Không |

Lý do giữ nhóm thứ hai: một người tắt thông báo rồi không biết mình vừa bị trừ tiền hay tài khoản bị khoá là trải nghiệm rất tệ. Các dịch vụ thực tế đều phân biệt hai nhóm này.

Người chưa từng thay đổi gì sẽ **mặc định được bật** — phải chủ động tắt nếu không muốn nhận.

### 2.4. Gửi email (phần đầu của chức năng 8.1)

Hệ thống đã gửi được email thật, với hai mẫu thư đã hoàn thiện:

**Thư nhắc học** — gửi cho người chưa học trong ngày, có nút dẫn thẳng về trang bài học.

**Thư xác nhận thanh toán** — gửi khi mua gói VIP thành công, ghi rõ số tiền và thời hạn gói.

Bốn điểm đáng chú ý trong cách làm:

**Email không bao giờ làm hỏng việc chính.** Nếu máy chủ email gặp sự cố, thông báo trong ứng dụng vẫn được tạo bình thường. Email chỉ là kênh phụ; thông báo trong ứng dụng mới là nơi lưu chính thức.

**Tự thử lại khi lỗi tạm thời.** Gửi thất bại sẽ được thử lại 3 lần, chờ lâu dần giữa các lần (1 giây, 5 giây, 25 giây). Phần lớn sự cố gửi mail chỉ là tạm thời, thử lại là xong.

**Không gửi thư thiếu thông tin.** Nếu lỡ thiếu dữ liệu, hệ thống báo lỗi và dừng thay vì gửi một bức thư kiểu "Chào ," cho người dùng.

**An toàn với tên có ký tự đặc biệt.** Tên người dùng lấy từ form đăng ký nên có thể chứa ký tự gây lỗi hiển thị hoặc nguy hiểm — hệ thống đã xử lý.

Nội dung thư xác nhận VIP được viết trung tính có chủ đích: *"Quyền VIP sẽ được kích hoạt trong ít phút"* thay vì khẳng định *"bạn đã là VIP"*. Vì việc nâng cấp do service khác xử lý song song, hai bên có thể lệch nhau vài giây, và hứa chắc chắn sẽ có lúc thành nói sai.

### 2.5. Môi trường phát triển

Đã dựng **Mailpit** — một máy chủ email giả chạy trên máy lập trình viên. Nó nhận mọi thư và hiển thị tại một trang web thay vì gửi ra ngoài thật, nên cả nhóm thử nghiệm thoải mái mà không lo gửi nhầm cho người thật.

---

## 3. Phần nền tảng đã dựng

Ngoài các chức năng người dùng thấy, còn những phần nền cần thiết:

**Cơ sở dữ liệu** — ba bảng đã tạo trên Supabase: danh sách thông báo, tuỳ chọn của từng người, và một bảng chống trùng lặp (giải thích ở mục 4).

**Quản lý thay đổi cấu trúc dữ liệu** — dùng công cụ Alembic giống các service khác trong nhóm, để mọi thay đổi cấu trúc đều có lịch sử và có thể lùi lại.

**Tài liệu kỹ thuật** — hai tài liệu đặc tả chi tiết cho toàn bộ module, làm cơ sở cho các phần còn lại.

**Kiểm thử tự động** — 29 bài kiểm tra chạy sau mỗi lần sửa code, trong đó 18 bài chạy trên cơ sở dữ liệu thật chứ không giả lập. Nếu ai đó vô tình làm hỏng một chức năng, hệ thống báo ngay.

---

## 4. Ba vấn đề kỹ thuật đã xử lý

Phần này ghi lại để những người làm sau không gặp lại.

### Chống gửi thông báo trùng

Khi người dùng thanh toán, service thanh toán gửi tín hiệu cho chúng tôi để tạo thông báo. Tín hiệu này **có thể bị gửi lại nhiều lần** nếu hệ thống gặp sự cố giữa chừng — đây là cách thiết kế có chủ đích, vì thà gửi thừa còn hơn mất tín hiệu.

Hậu quả nếu không xử lý: người dùng nhận hai thông báo "Thanh toán thành công" cho cùng một giao dịch.

Giải pháp: một bảng ghi lại những tín hiệu đã xử lý. Tín hiệu đến lần hai sẽ bị nhận ra và bỏ qua.

### Lỗi cập nhật cấu trúc dữ liệu bị huỷ âm thầm

Phát hiện một lỗi khiến việc cập nhật cấu trúc cơ sở dữ liệu **báo thành công nhưng thực tế không có gì thay đổi**. Loại lỗi này rất khó phát hiện vì không có thông báo lỗi nào.

Đã sửa cho service của mình. **Service Account cũng đang mắc lỗi tương tự** — cần báo cho Long và Đức.

### Ba lỗi khiến hệ thống kiểm tra tự động không chạy

Khi thêm service thứ hai vào hệ thống, ba công cụ kiểm tra tự động đồng loạt báo lỗi. Đã tìm ra nguyên nhân và sửa ở cấp độ chung cho cả nhóm, nên service của Hà sẽ không gặp lại khi gộp code.

---

## 5. Công việc còn lại

| Việc | Mô tả | Phụ thuộc |
|---|---|---|
| Nhắc học tự động 20:00 | Mỗi tối tìm người chưa học trong ngày và gửi nhắc nhở | Không — làm được ngay |
| Nhận tín hiệu từ service khác | Tạo thông báo khi có thanh toán, hết hạn VIP, khoá tài khoản | Chờ Long gộp code |
| Gợi ý bài học (cơ bản) | Dựa trên trình độ và điểm số gần đây | Cần hỏi Hà hai câu |
| Gợi ý bài học (nâng cao) | Dùng dữ liệu học viên tương tự — điểm nhấn khi bảo vệ | Làm sau |
| Hoàn thiện kiểm thử, tài liệu API | | Cuối cùng |

---

## 6. Hai câu cần hỏi các bạn khác

**Hỏi Hà:** Khi học viên làm lại một bài đã học, thời gian hoàn thành có được cập nhật không, hay chỉ cập nhật khi đạt điểm cao hơn?

*Vì sao quan trọng:* chức năng nhắc học dựa vào mốc thời gian này để biết ai đã học hôm nay. Nếu chỉ cập nhật khi điểm cao hơn, người học lại mà điểm thấp hơn sẽ bị tính nhầm là "chưa học" và nhận nhắc nhở sai.

**Hỏi Hà:** Khi một bài học được duyệt và xuất bản, có gửi tín hiệu cho các service khác không?

*Vì sao quan trọng:* nếu không, thông báo "Có bài học mới" sẽ không bao giờ xuất hiện. Bảng phân công không nói rõ điểm này.

---

## 7. Phối hợp với các bạn khác

Đã rà soát code của Long về phần gửi tín hiệu thanh toán. **Anh ấy làm đúng chuẩn** — cách đánh số tín hiệu đảm bảo cơ chế chống trùng của chúng tôi hoạt động. Không cần trao đổi thêm.

Phần khung sườn dùng chung của Đức cũng đã được áp dụng: xác thực người dùng, định dạng thông báo lỗi, ghi log đều dùng chung với cả nhóm thay vì tự viết riêng.
