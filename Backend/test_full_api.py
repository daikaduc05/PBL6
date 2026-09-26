# ruff: noqa
import sys
import httpx


class DummyConsole:
    def print(self, *args, **kwargs):
        text = " ".join(map(str, args))
        # Remove rich tags
        import re

        text = re.sub(r"\[/?(?:bold )?(?:blue|green|red)\]", "", text)
        print(text, **kwargs)


console = DummyConsole()
BASE_URL = "http://localhost:8002/api/v1"


def auth_headers(role: str = "admin") -> dict:
    return {
        "X-User-Id": "12345678-1234-5678-1234-567812345678",
        "X-User-Roles": role,
        "X-User-Tier": "normal",
    }


def step(title: str):
    console.print(f"\n[bold blue]--- {title} ---[/bold blue]")


def check_status(response, expected: int, action: str):
    if response.status_code == expected:
        console.print(f"[green]✓ {action} thành công (HTTP {expected})[/green]")
    else:
        console.print(
            f"[red]✗ {action} thất bại. Expected {expected}, got {response.status_code}[/red]"
        )
        console.print(f"[red]Response: {response.text}[/red]")
        sys.exit(1)


def run_tests():
    client = httpx.Client(base_url=BASE_URL)

    import uuid

    uid = uuid.uuid4().hex[:6]

    # 1. CATEGORY API
    step("C1. Tạo Category 1")
    res = client.post(
        "/categories",
        json={"name": f"Cat 1 {uid}", "slug": f"cat-1-{uid}"},
        headers=auth_headers("admin"),
    )
    check_status(res, 201, "Tạo Category 1")
    cat1_id = res.json()["id"]

    step("C2. Tạo Category 2 (Làm con của Cat 1)")
    res = client.post(
        "/categories",
        json={"name": f"Cat 2 {uid}", "slug": f"cat-2-{uid}", "parent_id": cat1_id},
        headers=auth_headers("admin"),
    )
    check_status(res, 201, "Tạo Category 2")
    cat2_id = res.json()["id"]

    step("C3. Fetch List Category (Tree)")
    res = client.get("/categories")
    check_status(res, 200, "Get Categories Tree")
    data = res.json()
    assert len(data) >= 1
    console.print(f"Số lượng category cha: {len(data)}")

    step("C4. Fetch 1 Category cụ thể")
    res = client.get(f"/categories/{cat1_id}")
    check_status(res, 200, "Get Category 1 detail")

    step("C5. Cập nhật Category")
    res = client.put(
        f"/categories/{cat1_id}", json={"name": "Cat 1 Updated"}, headers=auth_headers("admin")
    )
    check_status(res, 200, "Update Category 1")

    # 2. LESSON API
    step("L1. Tạo Lesson mới")
    lesson_payload = {
        "category_id": cat2_id,
        "title": "Test Lesson",
        "body": "Nội dung bài học",
        "level": "medium",
        "access": "public",
    }
    res = client.post("/lessons", json=lesson_payload, headers=auth_headers("admin"))
    check_status(res, 201, "Tạo Lesson")
    lesson_id = res.json()["id"]

    step("L2. Sửa Lesson (DRAFT)")
    res = client.put(
        f"/lessons/{lesson_id}",
        json={"title": "Test Lesson Updated"},
        headers=auth_headers("admin"),
    )
    check_status(res, 200, "Update Lesson")

    step("L3. Fetch List Lesson")
    res = client.get("/lessons")
    check_status(res, 200, "Get Lessons list")
    console.print(f"Total lessons: {res.json()['total']}")

    step("L4. Fetch 1 Lesson")
    res = client.get(f"/lessons/{lesson_id}")
    check_status(res, 200, "Get Lesson detail")

    step("L5. Submit chờ duyệt")
    res = client.post(f"/lessons/{lesson_id}/submit", headers=auth_headers("editor"))
    check_status(res, 200, "Submit Lesson")

    step("L6. Kiểm tra lỗi sửa khi không DRAFT")
    res = client.put(
        f"/lessons/{lesson_id}", json={"title": "Fail Update"}, headers=auth_headers("editor")
    )
    check_status(res, 400, "Bắt lỗi Update khi PENDING")

    step("L7. Duyệt Lesson")
    res = client.post(f"/lessons/{lesson_id}/approve", headers=auth_headers("admin"))
    check_status(res, 200, "Approve Lesson")

    step("L8. Sửa Lesson access thành VIP")
    res = client.put(f"/lessons/{lesson_id}", json={"access": "vip"}, headers=auth_headers("admin"))
    # Wait, can only edit when DRAFT. Let's make a new lesson for VIP testing
    pass

    step("L8. Tạo Lesson VIP")
    vip_lesson_payload = {
        "category_id": cat2_id,
        "title": "Test VIP Lesson",
        "body": "Nội dung cực VIP, chỉ VIP mới thấy",
        "level": "hard",
        "access": "vip",
    }
    res = client.post("/lessons", json=vip_lesson_payload, headers=auth_headers("admin"))
    check_status(res, 201, "Tạo VIP Lesson")
    vip_lesson_id = res.json()["id"]

    # Approve VIP lesson
    client.post(f"/lessons/{vip_lesson_id}/submit", headers=auth_headers("editor"))
    client.post(f"/lessons/{vip_lesson_id}/approve", headers=auth_headers("admin"))

    step("L9. Fetch VIP Lesson (User Thường)")
    res = client.get(
        f"/lessons/{vip_lesson_id}",
        headers={"X-User-Id": "123", "X-User-Roles": "student", "X-User-Tier": "normal"},
    )
    check_status(res, 200, "Get VIP Lesson as Normal User")
    assert "tài khoản VIP" in res.json()["body"], "Body must be truncated for normal user"
    console.print("[green]✓ Nội dung đã bị che đối với User thường[/green]")

    step("L10. Fetch VIP Lesson (User VIP)")
    res = client.get(
        f"/lessons/{vip_lesson_id}",
        headers={"X-User-Id": "123", "X-User-Roles": "student", "X-User-Tier": "vip"},
    )
    check_status(res, 200, "Get VIP Lesson as VIP User")
    assert "cực VIP" in res.json()["body"], "Body must be visible for VIP user"
    console.print("[green]✓ Nội dung hiển thị đầy đủ đối với User VIP[/green]")

    # 3. TEARDOWN
    step("T0. Xoá VIP Lesson")
    client.delete(f"/lessons/{vip_lesson_id}", headers=auth_headers("admin"))
    step("T1. Xoá Lesson")
    res = client.delete(f"/lessons/{lesson_id}", headers=auth_headers("admin"))
    check_status(res, 204, "Delete Lesson")

    step("T2. Xoá Category 2 (Con)")
    res = client.delete(f"/categories/{cat2_id}", headers=auth_headers("admin"))
    check_status(res, 204, "Delete Category 2")

    step("T3. Xoá Category 1 (Cha)")
    res = client.delete(f"/categories/{cat1_id}", headers=auth_headers("admin"))
    check_status(res, 204, "Delete Category 1")

    console.print("\n[bold green]TẤT CẢ TEST ĐÃ PASS THÀNH CÔNG![/bold green]")


if __name__ == "__main__":
    run_tests()
