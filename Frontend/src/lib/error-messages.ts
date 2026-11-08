// Maps the backend's error.code (backend.md §7 envelope) to a Vietnamese,
// plain-language message — design-system.md §10: "never a raw backend
// error code." Codes not listed here fall back to a generic message.
const MESSAGES: Record<string, string> = {
  UNAUTHORIZED: "Email hoặc mật khẩu không đúng, hoặc phiên đăng nhập đã hết hạn.",
  NOT_FOUND: "Không tìm thấy thông tin yêu cầu.",
  CONFLICT: "Email này đã được đăng ký.",
  FORBIDDEN: "Bạn không có quyền thực hiện thao tác này.",
  VALIDATION_ERROR: "Thông tin nhập chưa hợp lệ, vui lòng kiểm tra lại.",
};

export function errorMessageFor(code: string | undefined): string {
  if (!code) return "Đã có lỗi xảy ra, vui lòng thử lại.";
  return MESSAGES[code] ?? "Đã có lỗi xảy ra, vui lòng thử lại.";
}
