import type { ReactNode } from "react";

// Spec §2 + implementation note: route ALL pilgrim UI through BigButton so the UX laws
// (huge target ≥80px, icon + one short word, high contrast) hold automatically.
export function BigButton({
  icon,
  label,
  labelHindi,
  onPress,
  variant = "primary",
  disabled = false,
}: {
  icon?: ReactNode;
  label: string;
  labelHindi: string;
  onPress: () => void;
  variant?: "primary" | "secondary";
  disabled?: boolean;
}) {
  return (
    <button className={`big-button ${variant}`} onClick={onPress} disabled={disabled}>
      {icon && <span className="big-button__icon">{icon}</span>}
      <span className="big-button__label-hi">{labelHindi}</span>
      <span className="big-button__label-en">{label}</span>
    </button>
  );
}
