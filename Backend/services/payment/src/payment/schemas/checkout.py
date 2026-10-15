import uuid
from typing import Literal

from pydantic import BaseModel

from payment.plans import PlanCode


class CheckoutRequest(BaseModel):
    plan_code: PlanCode
    payment_method: Literal["VNPAY", "MOMO"]


class CheckoutResponse(BaseModel):
    transaction_id: uuid.UUID
    redirect_url: str
    status: str
