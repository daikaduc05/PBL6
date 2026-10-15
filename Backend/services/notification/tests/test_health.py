"""Health probes and the error envelope."""

import pytest


async def test_health_is_up_without_touching_the_database(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_health_echoes_the_gateway_request_id(client):
    response = await client.get("/health", headers={"X-Request-Id": "req-123"})

    # One request stays traceable across services only if every hop reuses the
    # id the gateway assigned.
    assert response.headers["X-Request-Id"] == "req-123"


async def test_health_generates_a_request_id_when_none_is_given(client):
    response = await client.get("/health")

    assert response.headers.get("X-Request-Id")


@pytest.mark.parametrize("path", ["/health/ready"])
async def test_readiness_reports_503_when_the_database_is_unreachable(client, path):
    # conftest points DATABASE_URL at a host that is not running, so this
    # exercises the failure branch rather than the happy path.
    response = await client.get(path)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not ready"
    assert body["checks"]["database"].startswith("error:")
