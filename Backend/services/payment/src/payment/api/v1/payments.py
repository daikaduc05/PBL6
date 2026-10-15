"""T29 — HTTP layer only, no business logic (backend.md §3 layering rule).

    POST /api/v1/payments/checkout   authenticated -> { redirect_url }

"authenticated" means the gateway has verified the JWT and forwarded
X-User-Id (backend.md §7). There is no gateway yet (T08/T09), so until it
exists, set X-User-Id by hand when calling this directly — same interim
gap already noted on account service's protected endpoints (T22/T23).
"""

import uuid

from fastapi import APIRouter, Depends
from pbl6_common.deps import UserContext, get_current_user

from payment.deps import get_checkout_service
from payment.schemas.checkout import CheckoutRequest, CheckoutResponse
from payment.services.checkout_service import CheckoutService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    body: CheckoutRequest,
    user: UserContext = Depends(get_current_user),
    svc: CheckoutService = Depends(get_checkout_service),
):
    transaction = await svc.checkout(
        user_id=uuid.UUID(user.user_id),
        plan_code=body.plan_code,
        payment_method=body.payment_method,
    )
    return CheckoutResponse(
        transaction_id=transaction.id,
        redirect_url=svc.build_redirect_url(transaction),
        status=transaction.status,
    )
