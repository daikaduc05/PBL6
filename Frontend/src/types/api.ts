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

export type PlanCode = "VIP_1_MONTH";

export interface Plan {
  code: PlanCode;
  name: string;
  amount: number;
  duration_days: number;
}

// Mirrors Backend/services/payment/src/payment/plans.py's PLANS catalogue —
// the backend doesn't expose a GET /plans endpoint (ER diagram dropped the
// `plans` table), so the display catalogue lives here too. Collapsed to a
// single token-priced plan on purpose (see plans.py's docstring) so the
// team can rehearse the real SePay bank-transfer flow for close to
// nothing — price/duration must match that file exactly or the UI will
// show a different number than what's actually charged.
export const PLAN: Plan = {
  code: "VIP_1_MONTH",
  name: "Gói VIP",
  amount: 5000,
  duration_days: 30,
};

export interface CheckoutResponse {
  transaction_id: string;
  status: "PENDING" | "SUCCESS" | "FAILED";
  qr_code_url: string;
  transfer_content: string;
  amount: string;
  bank_account_number: string;
  bank_code: string;
}

// Backend/services/notification/src/notification/schemas/notification.py
// and models/message.py (MessageType).

/** Mirrors backend.md §6 routing keys one-for-one. The stable label the UI
 * keys icons and filters on — unlike `title`, which is display copy and may
 * be reworded at any time. */
export type NotificationType =
  | "STUDY_REMINDER"
  | "PAYMENT_SUCCEEDED"
  | "VIP_EXPIRED"
  | "ACCOUNT_LOCKED"
  | "ACCOUNT_UNLOCKED"
  | "LESSON_PUBLISHED";

export interface NotificationItem {
  id: string;
  title: string;
  content: string;
  type: NotificationType;
  is_read: boolean;
  created_at: string;
}

export interface NotificationPage {
  items: NotificationItem[];
  /** Rows matching the current filter. */
  total: number;
  page: number;
  size: number;
  /** Unread total, ignoring the filter — this is what the bell shows. */
  unread_count: number;
}

export interface NotificationSettings {
  enable_daily_reminder: boolean;
  /** Local hour 0-23, Asia/Ho_Chi_Minh. */
  reminder_hour: number;
  device_token: string | null;
}

/** device_token is deliberately absent: the mobile app owns it, and sending
 * the whole settings object from the web would wipe the push token every
 * time someone changed their reminder time. */
export interface UpdateNotificationSettings {
  enable_daily_reminder: boolean;
  reminder_hour: number;
}
