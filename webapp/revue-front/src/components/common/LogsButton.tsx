import type { LogsCount } from "../../api/types"
import { plural } from "../../domain/format"
import { LOG_LEVEL_ORDER, LOG_LEVELS, worstLogLevel } from "../../domain/statuts"
import { WaButton, WaIcon, WaTooltip } from "../../wa"

const VARIANTS = { ERROR: "danger", WARNING: "warning", INFO: "brand" } as const

/** Takes the color and icon of the most severe level present in the logs. */
export function LogsButton({
  cohorteId,
  logs,
  onOpen,
}: {
  cohorteId: number
  logs: LogsCount
  onOpen: () => void
}) {
  const worst = worstLogLevel(logs)
  const total = LOG_LEVEL_ORDER.reduce((sum, level) => sum + logs[level], 0)
  const detail =
    LOG_LEVEL_ORDER.filter((level) => logs[level])
      .map((level) =>
        plural(logs[level], LOG_LEVELS[level].label, LOG_LEVELS[level].plural),
      )
      .join(" · ") || "aucun log"
  const id = `logs-${cohorteId}`
  return (
    <>
      <WaButton
        id={id}
        size="small"
        appearance="outlined"
        variant={worst ? VARIANTS[worst] : "neutral"}
        className={`logs-btn${worst ? ` lv-${worst}` : ""}`}
        onClick={onOpen}
      >
        {worst && <WaIcon slot="start" name={LOG_LEVELS[worst].icon} />}
        Logs <span className="mono">{total}</span>
      </WaButton>
      <WaTooltip for={id}>{detail}</WaTooltip>
    </>
  )
}
