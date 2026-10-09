import { useState } from "react"

import { useLogs } from "../../api/queries"
import { formatDateTime } from "../../domain/format"
import { LOG_LEVEL_ORDER, LOG_LEVELS, type LogLevel } from "../../domain/statuts"
import { WaDrawer, WaSpinner } from "../../wa"
import { Pager } from "./Pager"
import { Pill } from "./Pill"

const PAGE_SIZE = 100

/** Side panel listing the SuggestionLog of a cohorte, by gravity. */
export function LogsDrawer({
  cohorteId,
  onClose,
}: {
  cohorteId: number | null
  onClose: () => void
}) {
  const [niveaux, setNiveaux] = useState<LogLevel[]>([])
  const [page, setPage] = useState(1)
  const logs = useLogs(cohorteId, { niveau: niveaux, page, page_size: PAGE_SIZE })

  const toggle = (level: LogLevel) => {
    setPage(1)
    setNiveaux((current) =>
      current.includes(level)
        ? current.filter((l) => l !== level)
        : [...current, level],
    )
  }

  return (
    <WaDrawer
      open={cohorteId !== null}
      label={`Logs de la cohorte #${cohorteId ?? ""}`}
      placement="end"
      className="logs-drawer"
      onWaAfterHide={onClose}
    >
      <div className="tgroup">
        {LOG_LEVEL_ORDER.map((level) => (
          <button
            key={level}
            type="button"
            className="chip"
            aria-pressed={niveaux.includes(level)}
            onClick={() => toggle(level)}
          >
            {LOG_LEVELS[level].plural}
          </button>
        ))}
        {logs.isFetching && <WaSpinner />}
      </div>
      {logs.error && <p className="error">{logs.error.message}</p>}
      {logs.data && (
        <>
          <table className="tbl">
            <thead>
              <tr>
                <th>Niveau</th>
                <th>Message</th>
                <th>Transformation</th>
                <th>Acteur</th>
                <th>Colonnes</th>
              </tr>
            </thead>
            <tbody>
              {logs.data.items.map((log) => {
                const level = LOG_LEVELS[log.niveau as LogLevel]
                return (
                  <tr key={log.id}>
                    <td>
                      {level ? (
                        <Pill tone={level.tone}>{level.label}</Pill>
                      ) : (
                        log.niveau
                      )}
                      <span className="sub">{formatDateTime(log.cree_le)}</span>
                    </td>
                    <td>{log.message}</td>
                    <td className="mono">{log.fonction_de_transformation}</td>
                    <td className="mono">
                      {log.identifiant_unique}
                      {log.suggestion_groupe_id && (
                        <span className="sub">groupe {log.suggestion_groupe_id}</span>
                      )}
                    </td>
                    <td className="mono">
                      {(log.origine_colonnes ?? []).join(", ")}
                      {log.destination_colonnes?.length ? (
                        <> → {log.destination_colonnes.join(", ")}</>
                      ) : null}
                      {log.origine_valeurs?.length ? (
                        <span className="sub">{log.origine_valeurs.join(" | ")}</span>
                      ) : null}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {!logs.data.items.length && <p className="muted">Aucun log.</p>}
          <Pager
            unit="logs"
            page={page}
            pageSize={PAGE_SIZE}
            total={logs.data.total}
            onPage={setPage}
          />
        </>
      )}
    </WaDrawer>
  )
}
