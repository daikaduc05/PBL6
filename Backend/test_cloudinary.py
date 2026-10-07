import httpx
import json

# 1. First, create a category and a lesson so we have a lesson_id
print("1. Creating a temporary lesson...")
client = httpx.Client(base_url="http://localhost:8002/api/v1")
headers = {
    "X-User-Id": "12345678-1234-5678-1234-567812345678",
    "X-User-Roles": "admin",
}

# Create Category
res = client.post("/categories", json={"name": "Test Cloudinary", "slug": "test-cloudinary"}, headers=headers)
if res.status_code == 400: # Maybe slug exists
    res = client.get("/categories")
    cat_id = res.json()[0]["id"]
else:
    cat_id = res.json()["id"]

# Create Lesson
res = client.post("/lessons", json={
    "category_id": cat_id,
    "title": "Cloudinary Lesson",
    "body": "Test",
    "level": "easy",
    "access": "public"
}, headers=headers)
lesson_id = res.json()["id"]

print(f"-> Created Lesson ID: {lesson_id}")

# 2. Get Presigned URL for Cloudinary
print("\n2. Getting Cloudinary Upload Signature...")
res = client.post("/media/presigned-url", json={
    "lesson_id": lesson_id,
    "kind": "image",
    "filename": "test-image.png",
    "content_type": "image/png",
    "bytes": 50000 
}, headers=headers)

if res.status_code != 201:
    print("Error:", res.text)
    exit(1)

data = res.json()
print("Presigned URL response:")
print(json.dumps(data, indent=2))

upload_url = data["url"]
upload_fields = data["fields"]
media_id = data["media_asset_id"]
cdn_url = data["cdn_url"]

# 3. Upload a test image to Cloudinary
print(f"\n3. Uploading a small 1x1 image to Cloudinary directly: {upload_url}")
# A 1x1 transparent PNG file
import base64
png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")

files = {"file": ("test-image.png", png_data, "image/png")}
res = httpx.post(upload_url, data=upload_fields, files=files)

print("Cloudinary response:", res.status_code)
if res.status_code == 200:
    print("Upload successful!")
    print("Uploaded media URL:", res.json()["secure_url"])
    print("Our DB CDN URL is :", cdn_url)
else:
    print("Upload failed:", res.text)

print("\n4. Getting Media for Lesson to verify DB")
res = client.get(f"/media/lessons/{lesson_id}")
print("Media for lesson:", json.dumps(res.json(), indent=2))

print("\n5. Testing Delete from Cloudinary")
res = client.delete(f"/media/{media_id}", headers=headers)
print("Delete response:", res.status_code)
if res.status_code == 204:
    print("Successfully deleted from DB and Cloudinary!")
