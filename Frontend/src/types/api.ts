// Hand-written to match the backend's Pydantic schemas exactly (no OpenAPI
// codegen pipeline exists yet — frontend.md's `npm run gen:api` is
// aspirational until the gateway's aggregated schema exists, T07). Keep
// these in sync by hand with:
//   Backend/services/account/src/account/schemas/{auth,user}.py
//   Backend/services/payment/src/payment/{plans,schemas/checkout}.py

export interface ApiError {
  error: {
    code: string;
    message: string;
    details: unknown;
    request_id: string;
  };
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: "CUSTOMER" | "EDITOR" | "ADMIN";
  status: "ACTIVE" | "INACTIVE" | "LOCKED";
  is_vip: boolean;
  vip_expired_at: string | null;
  created_at: string;
}

export type PlanCode = "VIP_1_MONTH" | "VIP_3_MONTHS" | "VIP_12_MONTHS";

export interface Plan {
  code: PlanCode;
  name: string;
  amount: number;
  duration_days: number;
}

// Mirrors Backend/services/payment/src/payment/plans.py's PLANS catalogue —
// the backend doesn't expose a GET /plans endpoint (ER diagram dropped the
// `plans` table), so the display catalogue lives here too. Prices/duration
// must match that file exactly or checkout amounts will look wrong even
// though the real charge (computed server-side) is always correct.
export const PLANS: Plan[] = [
  { code: "VIP_1_MONTH", name: "Gói VIP 1 tháng", amount: 299000, duration_days: 30 },
  { code: "VIP_3_MONTHS", name: "Gói VIP 3 tháng", amount: 799000, duration_days: 90 },
  { code: "VIP_12_MONTHS", name: "Gói VIP 12 tháng", amount: 2990000, duration_days: 365 },
];

export interface CheckoutResponse {
  transaction_id: string;
  status: "PENDING" | "SUCCESS" | "FAILED";
  qr_code_url: string;
  transfer_content: string;
  amount: string;
  bank_account_number: string;
  bank_code: string;
}
