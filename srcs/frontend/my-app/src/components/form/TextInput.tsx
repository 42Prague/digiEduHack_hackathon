import type { InputHTMLAttributes } from "react";

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function TextInput({ label, error, ...props }: TextInputProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
        {label}
      </label>
      <input
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
      />
      {error && (
        <p className="text-xs text-red-600 dark:text-red-400 mt-0.5">{error}</p>
      )}
    </div>
  );
}
