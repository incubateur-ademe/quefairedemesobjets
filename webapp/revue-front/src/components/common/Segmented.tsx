export type SegmentedOption = { value: string; label: string; count?: number }

/** Compact single choice (toolbar quick filters, view switch). */
export function Segmented({
  label,
  options,
  value,
  onChange,
}: {
  label: string
  options: SegmentedOption[]
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="tgroup">
      <span className="tlabel">{label}</span>
      <div className="seg" role="group" aria-label={label}>
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            aria-pressed={option.value === value}
            onClick={() => onChange(option.value)}
          >
            {option.label}
            {option.count !== undefined && <span className="n">{option.count}</span>}
          </button>
        ))}
      </div>
    </div>
  )
}
