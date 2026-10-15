"""MoMo IPN signature verification and acknowledgement.

Field order and algorithm are copied verbatim from MoMo's own published
docs (developers.momo.vn, "Processing payment result" / "HTTP Response
(IPN)" sections) — these came from the official site during T29/T30, not
guessed, so confidence here is high even without a live sandbox call.

Incoming IPN signature fields (in this exact order):
  accessKey, amount, callbackToken, extraData, message, orderId,
  orderInfo, orderType, partnerClientId, partnerCode, payType, requestId,
  responseTime, resultCode, transId

Our ack response must itself be signed, with a DIFFERENT, shorter field
list (also documented):
  accessKey, extraData, message, orderId, partnerCode, requestId,
  responseTime, resultCode
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

_IPN_FIELDS = (
    "accessKey",
    "amount",
    "callbackToken",
    "extraData",
    "message",
    "orderId",
    "orderInfo",
    "orderType",
    "partnerClientId",
    "partnerCode",
    "payType",
    "requestId",
    "responseTime",
    "resultCode",
    "transId",
)

_ACK_FIELDS = (
    "accessKey",
    "extraData",
    "message",
    "orderId",
    "partnerCode",
    "requestId",
    "responseTime",
    "resultCode",
)


def _raw_signature_string(payload: dict[str, Any], fields: tuple[str, ...], access_key: str) -> str:
    values = {**payload, "accessKey": access_key}
    return "&".join(f"{field}={values.get(field, '')}" for field in fields)


def verify_signature(payload: dict[str, Any], *, access_key: str, secret: str) -> bool:
    received = payload.get("signature", "")
    if not received:
        return False
    raw = _raw_signature_string(payload, _IPN_FIELDS, access_key)
    expected = hmac.new(secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)


def build_ack(
    *,
    partner_code: str,
    request_id: str,
    order_id: str,
    result_code: int,
    message: str,
    access_key: str,
    secret: str,
    extra_data: str = "",
) -> dict[str, Any]:
    response_time = int(time.time() * 1000)
    fields = {
        "accessKey": access_key,
        "extraData": extra_data,
        "message": message,
        "orderId": order_id,
        "partnerCode": partner_code,
        "requestId": request_id,
        "responseTime": response_time,
        "resultCode": result_code,
    }
    raw = _raw_signature_string(fields, _ACK_FIELDS, access_key)
    signature = hmac.new(secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return {
        "partnerCode": partner_code,
        "requestId": request_id,
        "orderId": order_id,
        "resultCode": result_code,
        "message": message,
        "responseTime": response_time,
        "extraData": extra_data,
        "signature": signature,
    }
