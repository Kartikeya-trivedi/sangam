// Big tappable single-select chips — the panic-friendly alternative to typing.
// Tap toggles selection; tapping the selected chip again clears it (all fields optional).
export interface Chip<T extends string> {
  value: T;
  label: string;
  icon?: string;
}

export function ChipGroup<T extends string>({
  chips,
  selected,
  onSelect,
  columns = 3,
}: {
  chips: Chip<T>[];
  selected?: T;
  onSelect: (value: T | undefined) => void;
  columns?: number;
}) {
  return (
    <div className="chip-group" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
      {chips.map((c) => {
        const active = c.value === selected;
        return (
          <button
            key={c.value}
            type="button"
            className={`chip ${active ? "chip--active" : ""}`}
            aria-pressed={active}
            onClick={() => onSelect(active ? undefined : c.value)}
          >
            {c.icon && <span className="chip__icon">{c.icon}</span>}
            <span className="chip__label">{c.label}</span>
          </button>
        );
      })}
    </div>
  );
}
