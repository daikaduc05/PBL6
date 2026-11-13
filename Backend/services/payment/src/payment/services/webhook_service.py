"""SePay webhook business logic — verify signature, match to a PENDING
transaction, apply idempotently, publish payment.succeeded.

Unlike VNPay/Momo, SePay has no "payment failed" callback: a bank
transfer either lands (exactly one `transferType: "in"` webhook) or
nothing ever arrives for that transaction, which just stays PENDING
forever (the frontend's polling UI is expected to eventually give up and
let the user retry checkout — not this service's concern). So there is
no FAILED path here, unlike the VNPay/Momo branches this replaces.
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import cast

from pbl6_common.errors import UnauthorizedError

from payment.config import PaymentSettings
from payment.models.transaction import Transaction
from payment.plans import PLANS, PlanCode
from payment.repositories.protocols import OutboxRepositoryProtocol, TransactionRepositoryProtocol
from payment.webhooks import sepay

logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(
        self,
        transactions: TransactionRepositoryProtocol,
        outbox: OutboxRepositoryProtocol,
        settings: PaymentSettings,
    ):
        self._transactions = transactions
        self._outbox = outbox
        self._settings = settings

    async def handle_sepay(
        self, raw_body: bytes, *, signature: str | None, timestamp: str | None
    ) -> dict[str, bool]:
        if not sepay.verify_signature(
            raw_body,
            signature=signature,
            timestamp=timestamp,
            secret=self._settings.sepay_webhook_secret,
        ):
            raise UnauthorizedError("Invalid SePay signature")

        payload = json.loads(raw_body)

        # Only an incoming transfer can ever confirm a payment — SePay
        # also reports the account's own outgoing transfers on the same
        # webhook URL.
        if payload.get("transferType") != "in":
            return {"success": True}

        transaction_id = sepay.extract_transaction_id(
            payload.get("content", "")
        ) or sepay.extract_transaction_id(payload.get("description", ""))
        if transaction_id is None:
            return {"success": True}  # not one of our transfers — ack, nothing to do

        transaction = await self._transactions.get_by_id(transaction_id)
        if transaction is None:
            return {"success": True}

        provider_ref = str(payload.get("id", ""))
        if transaction.provider_txn_ref == provider_ref:
            return {"success": True}  # already applied — idempotent redelivery

        transferred_amount = Decimal(str(payload.get("transferAmount", 0)))
        if transferred_amount != transaction.amount:
            # Wrong amount for this transaction's reference code — don't
            # apply it. Ack anyway so SePay doesn't retry forever; this
            # needs a human to look at, not an automatic retry loop.
            logger.warning(
                "sepay webhook: amount mismatch for %s (got %s, expected %s)",
                transaction_id,
                transferred_amount,
                transaction.amount,
            )
            return {"success": True}

        transaction.provider_txn_ref = provider_ref
        transaction.status = "SUCCESS"
        await self._transactions.save(transaction)
        await self._publish_succeeded(transaction)
        return {"success": True}

    async def _publish_succeeded(self, transaction: Transaction) -> None:
        # Written in the same DB transaction as the status update above —
        # see OutboxRepository's docstring for why that's the whole point.
        # Field names match backend.md §6's documented payment.succeeded
        # contract.
        plan = PLANS[cast(PlanCode, transaction.plan_code)]
        await self._outbox.create(
            aggregate_id=transaction.id,
            event_type="payment.succeeded",
            payload={
                "transaction_id": str(transaction.id),
                "user_id": str(transaction.user_id),
                "plan_id": transaction.plan_code,
                "amount_vnd": float(transaction.amount),
                "duration_days": plan["duration_days"],
            },
        )
