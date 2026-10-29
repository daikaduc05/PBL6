"""Checkout business logic — create a PENDING transaction and the VietQR
payment info the frontend displays for the payer to scan.

Unlike VNPay/Momo's redirect flow (or the old MOCK_PAYMENT shortcut this
replaces), there is no gateway API call at checkout time: SePay has
nothing to "initiate" — the QR code itself fully encodes account/amount/
content, and the payer's own banking app does the transfer. The
transaction only ever moves to SUCCESS later, when WebhookService
confirms SePay actually saw the money land (see that module).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TypedDict

from payment.config import PaymentSettings
from payment.models.transaction import Transaction
from payment.plans import PLANS, PlanCode
from payment.repositories.protocols import TransactionRepositoryProtocol
from payment.webhooks import sepay


class PaymentInfo(TypedDict):
    qr_code_url: str
    transfer_content: str
    amount: Decimal
    bank_account_number: str
    bank_code: str


class CheckoutService:
    def __init__(self, transactions: TransactionRepositoryProtocol, settings: PaymentSettings):
        self._transactions = transactions
        self._settings = settings

    async def checkout(self, *, user_id: uuid.UUID, plan_code: PlanCode) -> Transaction:
        plan = PLANS[plan_code]
        return await self._transactions.create(
            user_id=user_id,
            amount=plan["amount"],
            payment_method="SEPAY",
            plan_code=plan_code,
        )

    def build_payment_info(self, transaction: Transaction) -> PaymentInfo:
        content = sepay.transfer_content_for(transaction.id)
        qr_url = sepay.build_qr_url(
            account_number=self._settings.sepay_account_number,
            bank_code=self._settings.sepay_bank_code,
            amount=transaction.amount,
            content=content,
        )
        return {
            "qr_code_url": qr_url,
            "transfer_content": content,
            "amount": transaction.amount,
            "bank_account_number": self._settings.sepay_account_number,
            "bank_code": self._settings.sepay_bank_code,
        }
