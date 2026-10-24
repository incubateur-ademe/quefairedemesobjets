import { formatNumber } from "../../domain/format"
import { WaButton, WaIcon } from "../../wa"

/** « groupes 101–200 sur 315 · page 2/4 », Précédente / Suivante. */
export function Pager({
  unit,
  page,
  pageSize,
  total,
  onPage,
}: {
  unit: string
  page: number
  pageSize: number
  total: number
  onPage: (page: number) => void
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  const first = total ? (page - 1) * pageSize + 1 : 0
  const last = Math.min(total, page * pageSize)
  return (
    <nav className="pager" aria-label="Pagination">
      <span>
        {unit} {formatNumber(first)}–{formatNumber(last)} sur {formatNumber(total)} ·
        page {page}/{pages}
      </span>
      <WaButton
        size="small"
        appearance="outlined"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
      >
        <WaIcon slot="start" name="arrow-left" />
        Précédente
      </WaButton>
      <WaButton
        size="small"
        appearance="outlined"
        disabled={page >= pages}
        onClick={() => onPage(page + 1)}
      >
        Suivante
        <WaIcon slot="end" name="arrow-right" />
      </WaButton>
    </nav>
  )
}

export function PageSizeSelect({
  unit,
  sizes,
  value,
  onChange,
}: {
  unit: string
  sizes: number[]
  value: number
  onChange: (size: number) => void
}) {
  return (
    <div className="tgroup">
      <span className="tlabel" aria-hidden="true">
        Par page
      </span>
      <select
        aria-label={`Nombre de ${unit} par page`}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      >
        {sizes.map((size) => (
          <option key={size} value={size}>
            {size} {unit}
          </option>
        ))}
      </select>
    </div>
  )
}
