"""Health probes and the shared request-id middleware."""


async def test_health_is_up_without_touching_the_database(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_health_carries_a_request_id(client):
    response = await client.get("/health")

    # RequestIdMiddleware (pbl6_common) stamps every response, so one request
    # stays traceable across services.
    assert response.headers.get("X-Request-Id")
