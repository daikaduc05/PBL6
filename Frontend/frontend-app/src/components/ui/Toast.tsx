

type ToastProps = {
  open: boolean;
  message: string;
  type?: "success" | "error" | "info" | "warning";
  onClose: () => void;
};

const toastStyles = {
  success: "border-green-200 bg-green-50 text-green-800",
  error: "border-red-200 bg-red-50 text-red-800",
  info: "border-blue-200 bg-blue-50 text-blue-800",
  warning: "border-yellow-200 bg-yellow-50 text-yellow-800",
};

export default function Toast({
  open,
  message,
  type = "success",
  onClose,
}: ToastProps) {
  if (!open) return null;

  return (
    <div
      role="status"
      className={`fixed right-5 top-5 z-[60] flex items-center gap-4 rounded-lg border px-4 py-3 shadow-lg ${toastStyles[type]}`}
    >
      <span className="text-sm font-medium">{message}</span>

      <button
        type="button"
        onClick={onClose}
        aria-label="Close notification"
        className="font-semibold hover:opacity-70"
      >
        X
      </button>
    </div>
  );
}