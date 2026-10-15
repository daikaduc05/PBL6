"""Identity forwarded by the gateway."""

import uuid

import pytest

from notification.deps import get_current_user
from notification.errors import UnauthorizedError

USER_ID = "3f2504e0-4f89-41d3-9a0c-0305e82c3301"


async def test_parses_id_roles_and_tier():
    user = await get_current_user(
        x_user_id=USER_ID, x_user_roles="customer, ADMIN", x_user_tier="VIP"
    )

    assert user.id == uuid.UUID(USER_ID)
    assert user.roles == {"CUSTOMER", "ADMIN"}
    assert user.is_admin
    assert user.is_vip


async def test_defaults_to_non_vip_customer_when_headers_are_sparse():
    user = await get_current_user(x_user_id=USER_ID)

    assert user.roles == frozenset()
    assert not user.is_vip
    assert not user.is_admin


@pytest.mark.parametrize("header", [None, "", "not-a-uuid"])
async def test_rejects_missing_or_malformed_user_id(header):
    with pytest.raises(UnauthorizedError):
        await get_current_user(x_user_id=header)
