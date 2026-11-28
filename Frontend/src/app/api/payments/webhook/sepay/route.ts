import { NextRequest } from "next/server";

const PAYMENT_BASE = process.env.PAYMENT_SERVICE_URL ?? "http://localhost:8004/api/v1";
const BACKEND_TIMEOUT_MS = Number(process.env.BACKEND_TIMEOUT_MS ?? "8000");

/** Forwards incoming SePay webhook calls (preserving raw body & HMAC signature
 * headers) through the BFF Gateway to `payment-service:8004`, so a single
 * tunnel or ingress pointing at Frontend (:3000) can also deliver webhooks. */
export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  const signature = req.headers.get("x-sepay-signature") ?? "";
  const timestamp = req.headers.get("x-sepay-timestamp") ?? "";

  try {
    const res = await fetch(`${PAYMENT_BASE}/payments/webhook/sepay`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-sepay-signature": signature,
        "x-sepay-timestamp": timestamp,
      },
      body: rawBody,
      cache: "no-store",
      signal: AbortSignal.timeout(BACKEND_TIMEOUT_MS),
    });
    const text = await res.text();
    return new Response(text, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return Response.json(
      {
        error: {
          code: "SERVICE_UNAVAILABLE",
          message: "Không thể chuyển tiếp webhook thanh toán.",
          details: null,
          request_id: "",
        },
      },
      { status: 503 },
    );
  }
}

