"""Hardcoded VIP plan catalogue — stand-in for a `plans` table the team
dropped from the simplified payment schema (ER diagram decision, see
Backend/db/README.md). Revisit as a real table if plans need to change
without a deploy.

Prices match what the design mockups already show (Design/design-system.md
§10 checkout example: "299.000₫ · Gói VIP 1 tháng").
"""

from decimal import Decimal
from typing import Literal, TypedDict

PlanCode = Literal["VIP_1_MONTH", "VIP_3_MONTHS", "VIP_12_MONTHS"]


class Plan(TypedDict):
    amount: Decimal
    duration_days: int


PLANS: dict[PlanCode, Plan] = {
    "VIP_1_MONTH": {"amount": Decimal("299000"), "duration_days": 30},
    "VIP_3_MONTHS": {"amount": Decimal("799000"), "duration_days": 90},
    "VIP_12_MONTHS": {"amount": Decimal("2990000"), "duration_days": 365},
}
