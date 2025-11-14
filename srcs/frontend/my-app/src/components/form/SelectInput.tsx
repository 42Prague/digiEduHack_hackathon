import type { SelectHTMLAttributes, ReactNode } from "react";

interface SelectInputProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  error?: string;
  children: ReactNode;
}

export function SelectInput({
  label,
  error,
  children,
  ...props
}: SelectInputProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
        {label}
      </label>
      <select
        {...props}
        className={[
          "px-3 py-2 rounded border text-sm",
          "bg-white dark:bg-gray-900",
          "border-gray-300 dark:border-gray-700",
          "focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary",
          props.className ?? "",
        ]
          .join(" ")
          .trim()}
      >
        {children}
      </select>
      {error && (
        <p className="text-xs text-red-600 dark:text-red-400 mt-0.5">{error}</p>
      )}
    </div>
  );
}
