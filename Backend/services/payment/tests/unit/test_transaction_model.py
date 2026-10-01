"""T28 is schema + migration only — no business logic yet (that's T29).
This just locks down the mapping so a future change notices if it drifts
from Backend/db/04_payment.sql."""

from payment.models.transaction import Transaction


def test_transaction_maps_to_payment_schema():
    assert Transaction.__tablename__ == "transactions"
    assert Transaction.__table__.schema == "payment"


def test_transaction_columns_match_the_sql_baseline():
    columns = {c.name for c in Transaction.__table__.columns}
    assert columns == {"id", "user_id", "amount", "payment_method", "status", "created_at"}
