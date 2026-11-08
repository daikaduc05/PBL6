"""HTTP layer only, no business logic (backend.md §3 layering rule).

    POST /api/v1/payments/webhook/sepay   public, HMAC-signature verified

"public" — no X-User-Id check, SePay's HMAC signature is the only
authentication (verified before touching the transaction, per backend.md
§12's security checklist: "verify the provider signature before parsing
the body"). Needs the raw request bytes — not a pydantic-parsed body —
since the signature is computed over them exactly as sent; re-serializing
JSON can change the bytes and silently break verification.
"""

from fastapi import APIRouter, Depends, Request

from payment.deps import get_webhook_service
from payment.services.webhook_service import WebhookService

router = APIRouter(prefix="/payments/webhook", tags=["payments"])


@router.post("/sepay")
async def webhook_sepay(
    request: Request,
    svc: WebhookService = Depends(get_webhook_service),
):
    raw_body = await request.body()
    return await svc.handle_sepay(
        raw_body,
        signature=request.headers.get("x-sepay-signature"),
        timestamp=request.headers.get("x-sepay-timestamp"),
    )
