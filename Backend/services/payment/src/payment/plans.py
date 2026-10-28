"""Hardcoded VIP plan catalogue — stand-in for a `plans` table the team
dropped from the simplified payment schema (ER diagram decision, see
Backend/db/README.md). Revisit as a real table if plans need to change
without a deploy.

Collapsed to a single plan at a token 5.000₫ price point deliberately —
this lets the team run a real, live bank-transfer demo (actual money,
actual SePay webhook, not a simulated one) for close to nothing, which a
299.000₫ plan made impractical to rehearse more than once or twice. 5.000₫
(not 1.000₫) because some transfer apps (e.g. MoMo) reject transfers
below their own minimum. Restore the multi-plan catalogue (prices
commented below) once the demo no longer needs real transfers to be
cheap.
"""

from decimal import Decimal
from typing import Literal, TypedDict

PlanCode = Literal["VIP_1_MONTH"]


class Plan(TypedDict):
    amount: Decimal
    duration_days: int


PLANS: dict[PlanCode, Plan] = {
    "VIP_1_MONTH": {"amount": Decimal("5000"), "duration_days": 30},
    # Previous catalogue, restore when real pricing is needed again:
    # "VIP_3_MONTHS": {"amount": Decimal("799000"), "duration_days": 90},
    # "VIP_12_MONTHS": {"amount": Decimal("2990000"), "duration_days": 365},
}
