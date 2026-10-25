import uuid
from decimal import Decimal

from pydantic import BaseModel

from payment.plans import PlanCode


class CheckoutRequest(BaseModel):
    plan_code: PlanCode


class CheckoutResponse(BaseModel):
    transaction_id: uuid.UUID
    status: str
    qr_code_url: str
    transfer_content: str
    amount: Decimal
    bank_account_number: str
    bank_code: str
