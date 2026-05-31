import type { ButtonHTMLAttributes, ReactNode } from "react";

type TooltipButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  tooltip: string;
  icon?: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "danger";
};

export function TooltipButton({
  tooltip,
  icon,
  variant = "secondary",
  children,
  className = "",
  ...props
}: TooltipButtonProps) {
  return (
    <button
      {...props}
      className={`tooltip-button ${variant} ${className}`}
      title={tooltip}
      aria-label={props["aria-label"] ?? tooltip}
      data-tooltip={tooltip}
    >
      {icon}
      {children ? <span>{children}</span> : null}
    </button>
  );
}
