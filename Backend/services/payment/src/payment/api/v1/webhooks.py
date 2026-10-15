"""T30 — HTTP layer only, no business logic (backend.md §3 layering rule).

    POST /api/v1/payments/webhook/{provider}   public, signature-verified

"public" — no X-User-Id check, the provider's HMAC signature is the only
authentication (verified before touching the transaction, per backend.md
§12's security checklist: "verify the provider signature before parsing
the body"). Unknown provider or a bad signature are rejected outright
(404 / 401); a valid signature for an unknown order still gets a 200 with
a provider-specific "not found" ack — that's what the gateway's own retry
logic expects, not an HTTP error.
"""

from fastapi import APIRouter, Depends, Request
from pbl6_common.errors import NotFoundError

from payment.deps import get_webhook_service
from payment.services.webhook_service import WebhookService

router = APIRouter(prefix="/payments/webhook", tags=["payments"])


@router.post("/{provider}")
async def webhook(
    provider: str,
    request: Request,
    svc: WebhookService = Depends(get_webhook_service),
):
    normalized = provider.strip().upper()
    if normalized == "VNPAY":
        # VNPay's IPN is conventionally delivered as query parameters.
        params = dict(request.query_params)
        return await svc.handle_vnpay(params)
    if normalized == "MOMO":
        payload = await request.json()
        return await svc.handle_momo(payload)
    raise NotFoundError(f"Unknown payment provider: {provider}")
