import clsx from "clsx";

/**
 * RetroButton — Rectangular, sharp-edged button with glow effects.
 *
 * @param {"primary"|"secondary"|"ghost"|"icon"} variant
 */
export default function RetroButton({
  children,
  variant = "primary",
  className,
  disabled = false,
  ...rest
}) {
  return (
    <button
      className={clsx("btn", `btn--${variant}`, className)}
      disabled={disabled}
      {...rest}
    >
      {children}
    </button>
  );
}
