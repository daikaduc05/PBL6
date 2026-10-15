"""T30 business logic — verify signature, apply idempotently, acknowledge.

Both providers are expected to echo back our own transaction id as their
order reference (VNPay's vnp_TxnRef / MoMo's orderId) — the same id this
service would hand the gateway at checkout time once real integration
exists. T29's mock path never calls a real gateway, so there is no live
round-trip to test this against; see T29/T30's module docstrings for why
(no working sandbox credentials for either provider).
"""

from __future__ import annotations

import uuid

from pbl6_common.errors import UnauthorizedError

from payment.config import PaymentSettings
from payment.models.transaction import Transaction
from payment.repositories.protocols import TransactionRepositoryProtocol
from payment.webhooks import momo, vnpay


class WebhookService:
    def __init__(self, transactions: TransactionRepositoryProtocol, settings: PaymentSettings):
        self._transactions = transactions
        self._settings = settings

    async def handle_vnpay(self, params: dict[str, str]) -> dict[str, str]:
        if not vnpay.verify_signature(params, secret=self._settings.vnpay_hash_secret):
            raise UnauthorizedError("Invalid VNPay signature")

        transaction = await self._find_transaction(params.get("vnp_TxnRef", ""))
        if transaction is None:
            return vnpay.build_ack(success=False, message="Order not found")

        provider_ref = params.get("vnp_TransactionNo", "")
        if transaction.provider_txn_ref == provider_ref:
            return vnpay.build_ack(success=True, message="Confirm Success")  # already applied

        transaction.provider_txn_ref = provider_ref
        transaction.status = "SUCCESS" if params.get("vnp_ResponseCode") == "00" else "FAILED"
        await self._transactions.save(transaction)
        # TODO(T31): publish payment.succeeded via the outbox once it exists
        # (same gap noted in T29's checkout — not wired up yet).
        return vnpay.build_ack(success=True, message="Confirm Success")

    async def handle_momo(self, payload: dict) -> dict:
        if not momo.verify_signature(
            payload,
            access_key=self._settings.momo_access_key,
            secret=self._settings.momo_secret_key,
        ):
            raise UnauthorizedError("Invalid MoMo signature")

        order_id = str(payload.get("orderId", ""))
        partner_code = str(payload.get("partnerCode", ""))
        request_id = str(payload.get("requestId", ""))

        def ack(*, result_code: int, message: str) -> dict:
            return momo.build_ack(
                partner_code=partner_code,
                request_id=request_id,
                order_id=order_id,
                result_code=result_code,
                message=message,
                access_key=self._settings.momo_access_key,
                secret=self._settings.momo_secret_key,
            )

        transaction = await self._find_transaction(order_id)
        if transaction is None:
            return ack(result_code=1, message="Order not found")

        provider_ref = str(payload.get("transId", ""))
        if transaction.provider_txn_ref == provider_ref:
            return ack(result_code=0, message="Already processed")

        transaction.provider_txn_ref = provider_ref
        transaction.status = "SUCCESS" if int(payload.get("resultCode", -1)) == 0 else "FAILED"
        await self._transactions.save(transaction)
        # TODO(T31): same gap as the VNPay branch above.
        return ack(result_code=0, message="Confirm Success")

    async def _find_transaction(self, ref: str) -> Transaction | None:
        try:
            transaction_id = uuid.UUID(ref)
        except (ValueError, AttributeError, TypeError):
            return None
        return await self._transactions.get_by_id(transaction_id)
