import type { FormEventHandler, ReactNode } from "react";

type FormProps = {
  title?: string;
  description?: string;
  onSubmit?: FormEventHandler<HTMLFormElement>;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export default function Form({
  title,
  description,
  onSubmit,
  children,
  actions,
  className = "",
}: FormProps) {
  return (
    <form
      onSubmit={onSubmit}
      className={`rounded-xl border border-gray-200 bg-white p-6 shadow-sm ${className}`}
    >
      {(title || description) && (
        <div className="mb-5">
          {title && (
            <h2 className="text-lg font-semibold text-gray-900">
              {title}
            </h2>
          )}

          {description && (
            <p className="mt-1 text-sm text-gray-500">
              {description}
            </p>
          )}
        </div>
      )}

      <div>{children}</div>

      {actions && (
        <div className="mt-6 flex flex-wrap justify-end gap-3">
          {actions}
        </div>
      )}
    </form>
  );
}