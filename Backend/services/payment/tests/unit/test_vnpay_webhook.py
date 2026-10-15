"""Pure function tests — construct a payload + signature ourselves using
the same algorithm, then verify our own verifier accepts/rejects it
correctly. This proves internal consistency of the implementation; it does
not prove the algorithm matches VNPay's real behaviour (no live sandbox —
see T30's commit)."""

from __future__ import annotations

from payment.webhooks import vnpay

SECRET = "test-vnpay-hash-secret"


def signed_params(**extra: str) -> dict[str, str]:
    base = {
        "vnp_TxnRef": "11c7030b-b350-42ed-a449-6c8ec38bfd1d",
        "vnp_Amount": "29900000",
        "vnp_ResponseCode": "00",
        "vnp_TransactionNo": "14512345",
        **extra,
    }
    base["vnp_SecureHash"] = vnpay.compute_signature(base, secret=SECRET)
    return base


def test_verify_signature_accepts_correctly_signed_params():
    params = signed_params()
    assert vnpay.verify_signature(params, secret=SECRET) is True


def test_verify_signature_rejects_tampered_amount():
    params = signed_params()
    params["vnp_Amount"] = "100"  # tampered after signing
    assert vnpay.verify_signature(params, secret=SECRET) is False


def test_verify_signature_rejects_wrong_secret():
    params = signed_params()
    assert vnpay.verify_signature(params, secret="wrong-secret") is False


def test_verify_signature_rejects_missing_hash():
    assert vnpay.verify_signature({"vnp_TxnRef": "x"}, secret=SECRET) is False


def test_build_ack_shape():
    assert vnpay.build_ack(success=True, message="Confirm Success") == {
        "RspCode": "00",
        "Message": "Confirm Success",
    }
    assert vnpay.build_ack(success=False, message="Order not found") == {
        "RspCode": "99",
        "Message": "Order not found",
    }
