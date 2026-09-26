import asyncio
from fastapi.testclient import TestClient
from content.main import app

client = TestClient(app)
try:
    response = client.get("/api/v1/lessons")
    print(response.status_code)
    print(response.json())
except Exception as e:
    import traceback
    traceback.print_exc()
