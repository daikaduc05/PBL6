"""T29 business logic — create a transaction and return a redirect URL.

Only MOCK_PAYMENT=true is implemented for now. There is no working real
VNPay/Momo sandbox available: VNPay's merchant account hit a dead end when
they migrated to their new unified "VNPAY ID" login (the old merchantv2
account doesn't carry over, and support wasn't reachable in time); Momo's
API requires a real registered business account to even get sandbox keys —
their public docs show the request/response shape but not usable
credentials. Writing real gateway signing code with no way to verify it
against a live sandbox would risk shipping a silent bug (wrong signature
algorithm, wrong field, ...) that nothing here could catch.

So: MOCK_PAYMENT (default true) marks the transaction SUCCESS immediately
and skips the real gateway round-trip entirely — this is backend.md's own
documented fallback for exactly this situation, not a shortcut invented
here. Swapping in a real gateway later only touches this one method.
"""

from __future__ import annotations

import uuid

from pbl6_common.errors import AppError

from payment.config import PaymentSettings
from payment.models.transaction import Transaction
from payment.plans import PLANS, PlanCode
from payment.repositories.protocols import OutboxRepositoryProtocol, TransactionRepositoryProtocol


class PaymentNotConfiguredError(AppError):
    status_code = 503
    code = "PAYMENT_GATEWAY_NOT_CONFIGURED"


class CheckoutService:
    def __init__(
        self,
        transactions: TransactionRepositoryProtocol,
        outbox: OutboxRepositoryProtocol,
        settings: PaymentSettings,
    ):
        self._transactions = transactions
        self._outbox = outbox
        self._settings = settings

    async def checkout(
        self, *, user_id: uuid.UUID, plan_code: PlanCode, payment_method: str
    ) -> Transaction:
        plan = PLANS[plan_code]
        transaction = await self._transactions.create(
            user_id=user_id,
            amount=plan["amount"],
            payment_method=payment_method,
            plan_code=plan_code,
        )

        if not self._settings.mock_payment:
            raise PaymentNotConfiguredError(
                "Real VNPay/Momo integration is not available yet — "
                "set MOCK_PAYMENT=true to use the mock checkout flow"
            )

        # Mock mode: no real gateway call, mark as already paid.
        transaction.status = "SUCCESS"
        await self._transactions.save(transaction)
        await self._publish_succeeded(transaction, plan_code)

        return transaction

    async def _publish_succeeded(self, transaction: Transaction, plan_code: PlanCode) -> None:
        # Written in the same DB transaction as the status update above —
        # see OutboxRepository's docstring for why that's the whole point.
        # Field names (plan_id, amount_vnd) match backend.md §6's
        # documented payment.succeeded contract, which T26 (account) and
        # the notification service already code against; plan_id's value
        # is our plan_code string since there is no `plans` table here.
        plan = PLANS[plan_code]
        await self._outbox.create(
            aggregate_id=transaction.id,
            event_type="payment.succeeded",
            payload={
                "transaction_id": str(transaction.id),
                "user_id": str(transaction.user_id),
                "plan_id": plan_code,
                "amount_vnd": float(transaction.amount),
                "duration_days": plan["duration_days"],
            },
        )

    def build_redirect_url(self, transaction: Transaction) -> str:
        base = self._settings.checkout_result_url
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}transaction_id={transaction.id}&status={transaction.status.lower()}"
