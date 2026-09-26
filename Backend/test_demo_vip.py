import uuid
import httpx
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("demo_vip.log", mode='w'),
        logging.StreamHandler()
    ]
)

BASE_URL = "http://localhost:8002/api/v1"

def auth_headers(role: str = "admin", tier: str = "normal") -> dict:
    return {
        "X-User-Id": "12345678-1234-5678-1234-567812345678",
        "X-User-Roles": role,
        "X-User-Tier": tier,
    }

def run_demo():
    client = httpx.Client(base_url=BASE_URL)
    uid = uuid.uuid4().hex[:4]

    logging.info("--- 1. TẠO 2 CATEGORIES ---")
    cat_a = client.post("/categories", json={"name": f"Cat A {uid}", "slug": f"cat-a-{uid}"}, headers=auth_headers("admin")).json()
    cat_b = client.post("/categories", json={"name": f"Cat B {uid}", "slug": f"cat-b-{uid}"}, headers=auth_headers("admin")).json()
    logging.info(f"Đã tạo Category A (ID: {cat_a['id']}) và Category B (ID: {cat_b['id']})")
    time.sleep(1)

    logging.info("--- 2. TẠO 6 LESSONS (Trạng thái PUBLISHED) ---")
    lessons_data = [
        {"title": "Lesson 1 (Public)", "body": "Nội dung public 1", "level": "easy", "access": "public", "category_id": cat_a["id"]},
        {"title": "Lesson 2 (Public)", "body": "Nội dung public 2", "level": "medium", "access": "public", "category_id": cat_a["id"]},
        {"title": "Lesson 3 (VIP)", "body": "Tuyệt chiêu IELTS (VIP 1)", "level": "hard", "access": "vip", "category_id": cat_a["id"]},
        {"title": "Lesson 4 (Public)", "body": "Nội dung public 4", "level": "easy", "access": "public", "category_id": cat_b["id"]},
        {"title": "Lesson 5 (VIP)", "body": "Tuyệt chiêu TOEIC (VIP 2)", "level": "hard", "access": "vip", "category_id": cat_b["id"]},
        {"title": "Lesson 6 (VIP)", "body": "Luyện thi đại học (VIP 3)", "level": "hard", "access": "vip", "category_id": cat_b["id"]},
    ]

    lesson_ids = []
    for data in lessons_data:
        res = client.post("/lessons", json=data, headers=auth_headers("admin"))
        l_id = res.json()["id"]
        lesson_ids.append(l_id)
        # Submit & Approve
        client.post(f"/lessons/{l_id}/submit", headers=auth_headers("editor"))
        client.post(f"/lessons/{l_id}/approve", headers=auth_headers("admin"))
        
        logging.info(f"Đã tạo & duyệt: {data['title']} - Access: {data['access'].upper()}")
        time.sleep(0.5)

    logging.info("--- 3. TEST FETCH DANH SÁCH (Normal User) ---")
    res_normal = client.get("/lessons", headers=auth_headers("student", tier="normal"))
    items = res_normal.json()["items"]
    
    for item in items:
        # Chỉ in các lesson vừa tạo
        if item["id"] in lesson_ids:
            logging.info(f"[Normal User] {item['title']} ({item['access'].upper()}) -> Body: '{item['body']}'")
            time.sleep(0.3)

    logging.info("--- 4. TEST FETCH DANH SÁCH (VIP User) ---")
    res_vip = client.get("/lessons", headers=auth_headers("student", tier="vip"))
    items = res_vip.json()["items"]
    
    for item in items:
        if item["id"] in lesson_ids:
            logging.info(f"[VIP User] {item['title']} ({item['access'].upper()}) -> Body: '{item['body']}'")
            time.sleep(0.3)

    logging.info("--- 5. DỌN DẸP TEARDOWN ---")
    for l_id in lesson_ids:
        client.delete(f"/lessons/{l_id}", headers=auth_headers("admin"))
    client.delete(f"/categories/{cat_a['id']}", headers=auth_headers("admin"))
    client.delete(f"/categories/{cat_b['id']}", headers=auth_headers("admin"))
    logging.info("Đã xoá sạch dữ liệu test!")

if __name__ == "__main__":
    run_demo()
