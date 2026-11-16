-- ==============================================================================
-- SEED DATA SCRIPT CHO HỆ THỐNG TỰ HỌC TIẾNG ANH PBL6
-- Thêm dữ liệu: Bài học đa trạng thái (PENDING, DRAFT, REJECTED), Quizzes, Questions, Options, Media
-- ==============================================================================

BEGIN;

-- 1. THÊM CÁC BÀI HỌC VỚI CÁC TRẠNG THÁI KHÁC NHAU (PENDING, DRAFT, REJECTED)
-- Danh mục:
-- Ngữ pháp: 'f6332c38-1175-4164-ae3b-bd0fc0b84564'
-- Từ vựng:  '07cf592c-1e10-44a1-9c15-b1b596dab83b'
-- Giao tiếp: '236b90b0-3c85-44fc-924e-7f0380899b38'
-- IELTS:     '44353739-9816-4b10-bde3-fb32d313c408'

-- 1.1. Bài học CHỜ DUYỆT (PENDING) - Hiển thị trong hàng đợi Moderation của Admin
INSERT INTO content.lessons (id, category_id, title, body, level, access, status, created_at, updated_at)
VALUES 
(
    'a1111111-1111-4111-a111-111111111111',
    '236b90b0-3c85-44fc-924e-7f0380899b38',
    'Tiếng Anh giao tiếp: Thủ tục Check-in và Xuất nhập cảnh tại sân bay',
    E'# Tiếng Anh giao tiếp tại Sân bay (Airport English)\n\nKhi đi du lịch hoặc công tác nước ngoài, việc giao tiếp tự tin tại sân bay là vô cùng quan trọng.\n\n## 1. Mẫu câu thường gặp tại quầy Check-in\n- **May I see your passport and ticket, please?** (Cho tôi xem hộ chiếu và vé máy bay của bạn được không?)\n- **Would you like a window seat or an aisle seat?** (Bạn muốn ngồi cạnh cửa sổ hay cạnh lối đi?)\n- **I have one suitcase to check and one carry-on bag.** (Tôi có một kiện hành lý ký gửi và một túi xách tay.)\n- **Your flight departs from Gate 12B at 14:30.** (Chuyến bay của bạn khởi hành từ Cửa 12B lúc 14:30.)\n\n## 2. Mẫu câu tại khu vực Hải quan (Customs & Immigration)\n- **What is the purpose of your visit?** (Mục đích chuyến đi của bạn là gì?)\n- **I am here for tourism / business.** (Tôi đến đây để du lịch / công tác.)\n- **How long do you intend to stay?** (Bạn dự định ở lại trong bao lâu?)\n- **I will be staying for two weeks at the Hilton Hotel.** (Tôi sẽ ở lại trong hai tuần tại khách sạn Hilton.)\n\n## 3. Từ vựng quan trọng\n- Boarding pass: Thẻ lên máy bay\n- Baggage claim: Khu vực nhận hành lý\n- Carry-on luggage: Hành lý xách tay\n- Departure lounge: Phòng chờ khởi hành',
    'MEDIUM',
    'PUBLIC',
    'PENDING',
    NOW() - INTERVAL '2 hours',
    NOW() - INTERVAL '2 hours'
),
(
    'a2222222-2222-4222-a222-222222222222',
    'f6332c38-1175-4164-ae3b-bd0fc0b84564',
    'Mệnh đề quan hệ rút gọn (Reduced Relative Clauses) chuyên sâu',
    E'# Mệnh đề quan hệ rút gọn (Reduced Relative Clauses)\n\nRút gọn mệnh đề quan hệ là điểm ngữ pháp quan trọng giúp câu văn súc tích, tự nhiên và nâng cao điểm số trong các bài thi IELTS/TOEIC.\n\n## 1. Rút gọn bằng V-ing (Khi mệnh đề ở thể chủ động)\nKhi đại từ quan hệ đóng vai trò chủ ngữ và động từ ở dạng chủ động, ta lược bỏ đại từ quan hệ và to-be (nếu có), chuyển động từ chính về dạng **V-ing**.\n- *Ví dụ gốc:* The man **who is standing** next to the door is my professor.\n- *Rút gọn:* The man **standing** next to the door is my professor.\n\n## 2. Rút gọn bằng V3/V-ed (Khi mệnh đề ở thể bị động)\nKhi động từ trong mệnh đề quan hệ mang nghĩa bị động, ta lược bỏ đại từ quan hệ và to-be, chỉ giữ lại quá khứ phân từ **V3/V-ed**.\n- *Ví dụ gốc:* The books **which were published** last year sold out quickly.\n- *Rút gọn:* The books **published** last year sold out quickly.\n\n## 3. Rút gọn bằng To-infinitive (Để chỉ mục đích hoặc sau số thứ tự)\nÁp dụng khi trước danh từ có các từ như *the first, the second, the only, the last*, hoặc dạng so sánh nhất.\n- *Ví dụ gốc:* Neil Armstrong was the first person **who walked** on the Moon.\n- *Rút gọn:* Neil Armstrong was the first person **to walk** on the Moon.',
    'HARD',
    'VIP',
    'PENDING',
    NOW() - INTERVAL '1 hour',
    NOW() - INTERVAL '1 hour'
),
(
    'a3333333-3333-4333-a333-333333333333',
    '44353739-9816-4b10-bde3-fb32d313c408',
    'IELTS Vocabulary: Chủ đề Môi trường và Biến đổi khí hậu (Environment)',
    E'# IELTS Academic Vocabulary: Environment & Sustainability\n\nChủ đề môi trường xuất hiện với tần suất rất cao trong IELTS Writing Task 2 và Speaking Part 3.\n\n## 1. Cụm từ và Collocations ăn điểm\n- **Carbon footprint:** Lượng khí thải carbon cá nhân/tổ chức tạo ra.\n- **Renewable energy sources:** Các nguồn năng lượng tái tạo (solar, wind).\n- **Fossil fuel depletion:** Sự cạn kiệt nhiên liệu hóa thạch.\n- **Ecological degradation:** Sự suy thoái hệ sinh thái.\n- **Combat global warming:** Chống lại sự nóng lên toàn cầu.\n- **Single-use plastic ban:** Lệnh cấm đồ nhựa dùng một lần.\n\n## 2. Ví dụ áp dụng vào bài luận Writing Task 2\n- *Câu ví dụ 1:* Governments should heavily subsidize **renewable energy sources** to accelerate the transition away from fossil fuels.\n- *Câu ví dụ 2:* Indiscriminate disposal of industrial waste causes irreversible **ecological degradation** to marine habitats.',
    'HARD',
    'VIP',
    'PENDING',
    NOW() - INTERVAL '30 minutes',
    NOW() - INTERVAL '30 minutes'
)
ON CONFLICT (id) DO UPDATE SET 
    title = EXCLUDED.title,
    body = EXCLUDED.body,
    status = EXCLUDED.status;

-- 1.2. Bài học BẢN NHÁP (DRAFT) - Dành cho Editor chỉnh sửa và gửi duyệt
INSERT INTO content.lessons (id, category_id, title, body, level, access, status, created_at, updated_at)
VALUES 
(
    'b1111111-1111-4111-b111-111111111111',
    '07cf592c-1e10-44a1-9c15-b1b596dab83b',
    '50 Cụm từ Collocations hay gặp nhất trong đề thi TOEIC',
    E'# 50 Collocations cốt lõi trong đề thi TOEIC\n\nNắm vững collocations giúp bạn chọn ngay đáp án đúng trong Part 5 mà không cần dịch từng từ.\n\n## Danh sách cụm từ phổ biến:\n1. **Conduct a survey:** Tiến hành một cuộc khảo sát\n2. **Meet the deadline:** Kịp thời hạn\n3. **Reach an agreement:** Đạt được thỏa thuận\n4. **Address an issue:** Giải quyết một vấn đề\n5. **Take into consideration:** Xem xét, cân nhắc điều gì\n\n*(Bài viết đang trong giai đoạn soạn thảo bổ sung thêm bài tập thực hành...)*',
    'MEDIUM',
    'PUBLIC',
    'DRAFT',
    NOW() - INTERVAL '5 hours',
    NOW() - INTERVAL '5 hours'
),
(
    'b2222222-2222-4222-b222-222222222222',
    'f6332c38-1175-4164-ae3b-bd0fc0b84564',
    'Câu gián tiếp (Reported Speech): Nguyên tắc lùi thì và chuyển đổi đại từ',
    E'# Câu gián tiếp trong tiếng Anh (Reported Speech)\n\nCâu gián tiếp dùng để thuật lại lời nói của một người khác mà không trích dẫn nguyên văn.\n\n## 1. Nguyên tắc lùi thì (Tense Backshift)\n- Hiện tại đơn (Present Simple) -> Quá khứ đơn (Past Simple)\n- Hiện tại tiếp diễn (Present Continuous) -> Quá khứ tiếp diễn (Past Continuous)\n- Hiện tại hoàn thành (Present Perfect) -> Quá khứ hoàn thành (Past Perfect)\n- Tương lai đơn (Will) -> Would\n- Can -> Could\n\n## 2. Thay đổi trạng từ chỉ thời gian và nơi chốn\n- Now -> Then\n- Today -> That day\n- Tomorrow -> The following day / the next day\n- Yesterday -> The day before / the previous day\n- Here -> There\n- This -> That',
    'EASY',
    'PUBLIC',
    'DRAFT',
    NOW() - INTERVAL '1 day',
    NOW() - INTERVAL '1 day'
)
ON CONFLICT (id) DO UPDATE SET 
    title = EXCLUDED.title,
    body = EXCLUDED.body,
    status = EXCLUDED.status;

-- 1.3. Bài học BỊ TỪ CHỐI (REJECTED) - Để kiểm thử filter Rejected
INSERT INTO content.lessons (id, category_id, title, body, level, access, status, created_at, updated_at)
VALUES 
(
    'c1111111-1111-4111-c111-111111111111',
    '236b90b0-3c85-44fc-924e-7f0380899b38',
    'Tổng hợp 20 thành ngữ tiếng Anh lóng (Slang Idioms) giới trẻ hay dùng',
    E'# English Slangs & Informal Expressions\n\nMột số từ lóng trong giao tiếp thường ngày của giới trẻ phương Tây:\n- **Hang out:** Đi chơi với bạn bè\n- **Crash:** Đi ngủ vì quá mệt\n- **Piece of cake:** Dễ như ăn kẹo\n\n*(Ghi chú kiểm duyệt: Nội dung bài học quá ngắn, chưa có ví dụ thực tế và giải thích văn cảnh. Vui lòng bổ sung đầy đủ ngữ liệu.)*',
    'EASY',
    'PUBLIC',
    'REJECTED',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '1 day'
)
ON CONFLICT (id) DO UPDATE SET 
    title = EXCLUDED.title,
    body = EXCLUDED.body,
    status = EXCLUDED.status;


-- 2. BỔ SUNG CÁC BỘ QUIZ & CÂU HỎI TRẮC NGHIỆM CHO CÁC BÀI HỌC
-- 2.1. Quiz cho bài: Câu bị động (Passive Voice) - ID: 3cd70200-dc30-4d05-a30f-2f7d7d8f1660
INSERT INTO learning.quizzes (id, lesson_id, title, created_at)
VALUES (
    'd0000001-0000-4000-a000-000000000001',
    '3cd70200-dc30-4d05-a30f-2f7d7d8f1660',
    'Bài tập trắc nghiệm: Câu bị động (Passive Voice)',
    NOW()
) ON CONFLICT (id) DO NOTHING;

INSERT INTO learning.questions (id, quiz_id, content, type)
VALUES 
(
    'd1000001-0000-4000-a100-000000000001',
    'd0000001-0000-4000-a000-000000000001',
    'The urgent report ___ by the project manager yesterday.',
    'SINGLE_CHOICE'
),
(
    'd1000001-0000-4000-a100-000000000002',
    'd0000001-0000-4000-a000-000000000001',
    'English ___ as a second language in many schools in Asia.',
    'SINGLE_CHOICE'
),
(
    'd1000001-0000-4000-a100-000000000003',
    'd0000001-0000-4000-a000-000000000001',
    'Look! A new suspension bridge ___ across the river right now.',
    'SINGLE_CHOICE'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO learning.options (id, question_id, content, is_correct)
VALUES 
-- Question 1 options
('f1000001-0001-4000-a100-000000000001', 'd1000001-0000-4000-a100-000000000001', 'was submitted', true),
('f1000001-0001-4000-a100-000000000002', 'd1000001-0000-4000-a100-000000000001', 'is submitted', false),
('f1000001-0001-4000-a100-000000000003', 'd1000001-0000-4000-a100-000000000001', 'submits', false),
('f1000001-0001-4000-a100-000000000004', 'd1000001-0000-4000-a100-000000000001', 'has submitted', false),
-- Question 2 options
('f1000002-0001-4000-a100-000000000001', 'd1000001-0000-4000-a100-000000000002', 'is taught', true),
('f1000002-0001-4000-a100-000000000002', 'd1000001-0000-4000-a100-000000000002', 'teaches', false),
('f1000002-0001-4000-a100-000000000003', 'd1000001-0000-4000-a100-000000000002', 'is teaching', false),
('f1000002-0001-4000-a100-000000000004', 'd1000001-0000-4000-a100-000000000002', 'taught', false),
-- Question 3 options
('f1000003-0001-4000-a100-000000000001', 'd1000001-0000-4000-a100-000000000003', 'is being built', true),
('f1000003-0001-4000-a100-000000000002', 'd1000001-0000-4000-a100-000000000003', 'is building', false),
('f1000003-0001-4000-a100-000000000003', 'd1000001-0000-4000-a100-000000000003', 'builds', false),
('f1000003-0001-4000-a100-000000000004', 'd1000001-0000-4000-a100-000000000003', 'has built', false)
ON CONFLICT (id) DO NOTHING;


-- 2.2. Quiz cho bài: Câu điều kiện loại 2 - ID: 7b2714f2-b785-4306-89f3-64c2bd8d2f33
INSERT INTO learning.quizzes (id, lesson_id, title, created_at)
VALUES (
    'd0000002-0000-4000-a000-000000000002',
    '7b2714f2-b785-4306-89f3-64c2bd8d2f33',
    'Bài tập trắc nghiệm: Câu điều kiện loại 2',
    NOW()
) ON CONFLICT (id) DO NOTHING;

INSERT INTO learning.questions (id, quiz_id, content, type)
VALUES 
(
    'd2000001-0000-4000-a200-000000000001',
    'd0000002-0000-4000-a000-000000000002',
    'If I ___ the lottery, I would buy a large villa by the beach.',
    'SINGLE_CHOICE'
),
(
    'd2000001-0000-4000-a200-000000000002',
    'd0000002-0000-4000-a000-000000000002',
    'If she ___ harder, she would achieve a higher IELTS score.',
    'SINGLE_CHOICE'
),
(
    'd2000001-0000-4000-a200-000000000003',
    'd0000002-0000-4000-a000-000000000002',
    'What would you do if you ___ stranded on an uninhabited island?',
    'SINGLE_CHOICE'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO learning.options (id, question_id, content, is_correct)
VALUES 
-- Question 1 options
('f2000001-0001-4000-a200-000000000001', 'd2000001-0000-4000-a200-000000000001', 'won', true),
('f2000001-0001-4000-a200-000000000002', 'd2000001-0000-4000-a200-000000000001', 'win', false),
('f2000001-0001-4000-a200-000000000003', 'd2000001-0000-4000-a200-000000000001', 'will win', false),
('f2000001-0001-4000-a200-000000000004', 'd2000001-0000-4000-a200-000000000001', 'have won', false),
-- Question 2 options
('f2000002-0001-4000-a200-000000000001', 'd2000001-0000-4000-a200-000000000002', 'studied', true),
('f2000002-0001-4000-a200-000000000002', 'd2000001-0000-4000-a200-000000000002', 'studies', false),
('f2000002-0001-4000-a200-000000000003', 'd2000001-0000-4000-a200-000000000002', 'will study', false),
('f2000002-0001-4000-a200-000000000004', 'd2000001-0000-4000-a200-000000000002', 'study', false),
-- Question 3 options
('f2000003-0001-4000-a200-000000000001', 'd2000001-0000-4000-a200-000000000003', 'were', true),
('f2000003-0001-4000-a200-000000000002', 'd2000001-0000-4000-a200-000000000003', 'are', false),
('f2000003-0001-4000-a200-000000000003', 'd2000001-0000-4000-a200-000000000003', 'will be', false),
('f2000003-0001-4000-a200-000000000004', 'd2000001-0000-4000-a200-000000000003', 'have been', false)
ON CONFLICT (id) DO NOTHING;


-- 2.3. Quiz cho bài: Mệnh đề quan hệ (Relative Clauses) - ID: e9304103-a0c0-4edf-9e25-af8394919530
INSERT INTO learning.quizzes (id, lesson_id, title, created_at)
VALUES (
    'd0000003-0000-4000-a000-000000000003',
    'e9304103-a0c0-4edf-9e25-af8394919530',
    'Bài tập trắc nghiệm: Mệnh đề quan hệ',
    NOW()
) ON CONFLICT (id) DO NOTHING;

INSERT INTO learning.questions (id, quiz_id, content, type)
VALUES 
(
    'd3000001-0000-4000-a300-000000000001',
    'd0000003-0000-4000-a000-000000000003',
    'The engineer ___ designed this groundbreaking software won the innovation prize.',
    'SINGLE_CHOICE'
),
(
    'd3000001-0000-4000-a300-000000000002',
    'd0000003-0000-4000-a000-000000000003',
    'The company is expanding into markets ___ have high growth potential.',
    'SINGLE_CHOICE'
),
(
    'd3000001-0000-4000-a300-000000000003',
    'd0000003-0000-4000-a000-000000000003',
    'The candidate ___ interview was outstanding received the job offer immediately.',
    'SINGLE_CHOICE'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO learning.options (id, question_id, content, is_correct)
VALUES 
-- Question 1 options
('f3000001-0001-4000-a300-000000000001', 'd3000001-0000-4000-a300-000000000001', 'who', true),
('f3000001-0001-4000-a300-000000000002', 'd3000001-0000-4000-a300-000000000001', 'which', false),
('f3000001-0001-4000-a300-000000000003', 'd3000001-0000-4000-a300-000000000001', 'whose', false),
('f3000001-0001-4000-a300-000000000004', 'd3000001-0000-4000-a300-000000000001', 'whom', false),
-- Question 2 options
('f3000002-0001-4000-a300-000000000001', 'd3000001-0000-4000-a300-000000000002', 'which', true),
('f3000002-0001-4000-a300-000000000002', 'd3000001-0000-4000-a300-000000000002', 'who', false),
('f3000002-0001-4000-a300-000000000003', 'd3000001-0000-4000-a300-000000000002', 'whom', false),
('f3000002-0001-4000-a300-000000000004', 'd3000001-0000-4000-a300-000000000002', 'where', false),
-- Question 3 options
('f3000003-0001-4000-a300-000000000001', 'd3000001-0000-4000-a300-000000000003', 'whose', true),
('f3000003-0001-4000-a300-000000000002', 'd3000001-0000-4000-a300-000000000003', 'who', false),
('f3000003-0001-4000-a300-000000000003', 'd3000001-0000-4000-a300-000000000003', 'whom', false),
('f3000003-0001-4000-a300-000000000004', 'd3000001-0000-4000-a300-000000000003', 'which', false)
ON CONFLICT (id) DO NOTHING;


-- 2.4. Quiz cho bài: Từ vựng công sở (Business English) - ID: 7c1bbc8a-e264-4fa7-a920-dca7910c60a3
INSERT INTO learning.quizzes (id, lesson_id, title, created_at)
VALUES (
    'd0000004-0000-4000-a000-000000000004',
    '7c1bbc8a-e264-4fa7-a920-dca7910c60a3',
    'Trắc nghiệm: Từ vựng tiếng Anh công sở',
    NOW()
) ON CONFLICT (id) DO NOTHING;

INSERT INTO learning.questions (id, quiz_id, content, type)
VALUES 
(
    'd4000001-0000-4000-a400-000000000001',
    'd0000004-0000-4000-a000-000000000004',
    'Cụm từ "to meet the deadline" có nghĩa là gì?',
    'SINGLE_CHOICE'
),
(
    'd4000001-0000-4000-a400-000000000002',
    'd0000004-0000-4000-a000-000000000004',
    'Từ nào dưới đây đồng nghĩa với "coworker"?',
    'SINGLE_CHOICE'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO learning.options (id, question_id, content, is_correct)
VALUES 
-- Question 1 options
('f4000001-0001-4000-a400-000000000001', 'd4000001-0000-4000-a400-000000000001', 'Hoàn thành công việc đúng thời hạn', true),
('f4000001-0001-4000-a400-000000000002', 'd4000001-0000-4000-a400-000000000001', 'Trễ hạn nộp báo cáo', false),
('f4000001-0001-4000-a400-000000000003', 'd4000001-0000-4000-a400-000000000001', 'Hủy bỏ dự án', false),
('f4000001-0001-4000-a400-000000000004', 'd4000001-0000-4000-a400-000000000001', 'Yêu cầu tăng lương', false),
-- Question 2 options
('f4000002-0001-4000-a400-000000000001', 'd4000001-0000-4000-a400-000000000002', 'colleague', true),
('f4000002-0001-4000-a400-000000000002', 'd4000001-0000-4000-a400-000000000002', 'competitor', false),
('f4000002-0001-4000-a400-000000000003', 'd4000001-0000-4000-a400-000000000002', 'employer', false),
('f4000002-0001-4000-a400-000000000004', 'd4000001-0000-4000-a400-000000000002', 'customer', false)
ON CONFLICT (id) DO NOTHING;


-- 3. BỔ SUNG MEDIA ASSETS CHO CÁC BÀI HỌC
-- Gán audio Cloudinary chất lượng cao cho các bài học giao tiếp & ngữ pháp
INSERT INTO content.media_assets (id, lesson_id, kind, s3_key, cdn_url, bytes)
VALUES 
(
    'e1111111-1111-4111-e111-111111111111',
    '2dbd3c85-5a5b-4f58-80a1-c1e8a0845029', -- Đặt phòng khách sạn
    'AUDIO',
    'lessons/2dbd3c85/hotel-booking-audio',
    'https://res.cloudinary.com/dr3wv6tee/video/upload/v1728362000/lessons/hotel-booking.mp3',
    786432
),
(
    'e2222222-2222-4222-e222-222222222222',
    '3cd70200-dc30-4d05-a30f-2f7d7d8f1660', -- Câu bị động
    'AUDIO',
    'lessons/3cd70200/passive-voice-audio',
    'https://res.cloudinary.com/dr3wv6tee/video/upload/v1728362000/lessons/passive-voice.mp3',
    655360
),
(
    'e3333333-3333-4333-e333-333333333333',
    'a1111111-1111-4111-a111-111111111111', -- Check-in sân bay (Pending)
    'AUDIO',
    'lessons/a1111111/airport-checkin-audio',
    'https://res.cloudinary.com/dr3wv6tee/video/upload/v1728362000/lessons/airport-checkin.mp3',
    892400
)
ON CONFLICT (id) DO NOTHING;

COMMIT;
