"""Locks down the mapping so a future change notices if it drifts from
Backend/db/04_payment.sql (same pattern as test_transaction_model.py)."""

from payment.models.outbox import OutboxEntry


def test_outbox_maps_to_payment_schema():
    assert OutboxEntry.__tablename__ == "outbox"
    assert OutboxEntry.__table__.schema == "payment"


def test_outbox_columns_match_the_sql_baseline():
    columns = {c.name for c in OutboxEntry.__table__.columns}
    assert columns == {
        "id",
        "aggregate_id",
        "event_type",
        "payload",
        "created_at",
        "published_at",
    }
