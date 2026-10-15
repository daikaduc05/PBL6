"""Pure function tests — same approach as test_vnpay_webhook.py."""

from __future__ import annotations

import hashlib
import hmac

from payment.webhooks import momo

ACCESS_KEY = "test-momo-access-key"
SECRET = "test-momo-secret-key"


def signed_ipn_payload(**extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "partnerCode": "MOMO",
        "orderId": "11c7030b-b350-42ed-a449-6c8ec38bfd1d",
        "requestId": "req-1",
        "amount": 299000,
        "orderInfo": "pay with MoMo",
        "orderType": "momo_wallet",
        "transId": 9876543210,
        "resultCode": 0,
        "message": "Success",
        "payType": "qr",
        "responseTime": 1700000000000,
        "extraData": "",
        "callbackToken": "",
        "partnerClientId": "",
        **extra,
    }
    raw = momo._raw_signature_string(payload, momo._IPN_FIELDS, ACCESS_KEY)
    payload["signature"] = hmac.new(SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return payload


def test_verify_signature_accepts_correctly_signed_payload():
    payload = signed_ipn_payload()
    assert momo.verify_signature(payload, access_key=ACCESS_KEY, secret=SECRET) is True


def test_verify_signature_rejects_tampered_result_code():
    payload = signed_ipn_payload()
    payload["resultCode"] = 0
    payload["resultCode"] = 1  # tampered after signing
    assert momo.verify_signature(payload, access_key=ACCESS_KEY, secret=SECRET) is False


def test_verify_signature_rejects_wrong_access_key():
    payload = signed_ipn_payload()
    assert momo.verify_signature(payload, access_key="wrong-key", secret=SECRET) is False


def test_verify_signature_rejects_missing_signature():
    assert momo.verify_signature({"orderId": "x"}, access_key=ACCESS_KEY, secret=SECRET) is False


def test_build_ack_signature_is_self_verifiable():
    ack = momo.build_ack(
        partner_code="MOMO",
        request_id="req-1",
        order_id="11c7030b-b350-42ed-a449-6c8ec38bfd1d",
        result_code=0,
        message="Confirm Success",
        access_key=ACCESS_KEY,
        secret=SECRET,
    )
    raw = momo._raw_signature_string(ack, momo._ACK_FIELDS, ACCESS_KEY)
    expected = hmac.new(SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
    assert ack["signature"] == expected
