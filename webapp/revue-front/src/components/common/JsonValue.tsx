/** Readable display of a JSON value (cohorte metadata, groupe contexte…):
 * tabular JSON is rendered as a table, objects as key / value lists. */

type Table = { columns: string[]; rows: { label: string; cells: unknown[] }[] }

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value)

const isScalar = (value: unknown) => value === null || typeof value !== "object"

/** Recognizes the tabular shapes produced by the pipelines:
 * - `{" ": [col…], row: [cell…], …}`: a header key with a blank name;
 * - `{row: [cell…], …}`: arrays of scalars of the same length;
 * - `[{col: cell, …}, …]`: a list of flat objects. */
export function toTable(value: unknown): Table | null {
  if (Array.isArray(value)) {
    if (!value.length || !value.every(isRecord)) {
      return null
    }
    const records = value as Record<string, unknown>[]
    if (!records.every((record) => Object.values(record).every(isScalar))) {
      return null
    }
    const columns = [...new Set(records.flatMap((record) => Object.keys(record)))]
    return {
      columns,
      rows: records.map((record, index) => ({
        label: String(index + 1),
        cells: columns.map((column) => record[column]),
      })),
    }
  }
  if (!isRecord(value)) {
    return null
  }
  const entries = Object.entries(value)
  if (
    !entries.length ||
    !entries.every(([, cells]) => Array.isArray(cells) && cells.every(isScalar))
  ) {
    return null
  }
  const header = entries.find(([key]) => key.trim() === "")
  const rows = entries.filter((entry) => entry !== header)
  const width =
    (header?.[1] as unknown[] | undefined)?.length ?? (rows[0][1] as unknown[]).length
  if (!rows.every(([, cells]) => (cells as unknown[]).length === width)) {
    return null
  }
  return {
    columns: header
      ? (header[1] as unknown[]).map(String)
      : Array.from({ length: width }, (_, i) => String(i + 1)),
    rows: rows.map(([label, cells]) => ({ label, cells: cells as unknown[] })),
  }
}

function Scalar({ value }: { value: unknown }) {
  if (value === null || value === undefined || value === "") {
    return <span className="faint">—</span>
  }
  if (typeof value === "boolean") {
    return <>{value ? "oui" : "non"}</>
  }
  return <>{String(value)}</>
}

export function JsonValue({ value }: { value: unknown }) {
  const table = toTable(value)
  if (table) {
    return (
      <table className="json-table">
        <thead>
          <tr>
            <th />
            {table.columns.map((column) => (
              <th key={column} className="num">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row) => (
            <tr key={row.label}>
              <th scope="row">{row.label}</th>
              {row.cells.map((cell, index) => (
                <td
                  key={index}
                  className={typeof cell === "number" ? "num" : undefined}
                >
                  <Scalar value={cell} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    )
  }
  if (isRecord(value)) {
    return <JsonEntries entries={Object.entries(value)} />
  }
  if (Array.isArray(value)) {
    return value.every(isScalar) ? (
      <>{value.map(String).join(", ")}</>
    ) : (
      <JsonEntries entries={value.map((item, index) => [String(index + 1), item])} />
    )
  }
  return <Scalar value={value} />
}

/** Key / value list, values rendered recursively. */
export function JsonEntries({ entries }: { entries: [string, unknown][] }) {
  return (
    <dl className="metagrid">
      {entries.map(([key, value]) => (
        <div key={key} className="metagrid__item">
          <dt>{key}</dt>
          <dd>
            <JsonValue value={value} />
          </dd>
        </div>
      ))}
    </dl>
  )
}
