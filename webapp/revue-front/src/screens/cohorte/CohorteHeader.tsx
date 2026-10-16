import type { CohorteDetail, Stats, Vue } from "../../api/types"
import { LogsButton } from "../../components/common/LogsButton"
import { CohorteStatutPill } from "../../components/common/Pill"
import { StackBar, totalOf } from "../../components/common/StackBar"
import { formatNumber } from "../../domain/format"
import { STATUT_ORDER, STATUTS } from "../../domain/statuts"
import { buildHref, Link, useRouter } from "../../router"
import { TYPE_ACTIONS } from "../../domain/statuts"

const ALWAYS_SHOWN = ["AVALIDER", "ATRAITER", "REJETEE"]

export function CohorteHeader({
  cohorte,
  onOpenLogs,
}: {
  cohorte: CohorteDetail
  onOpenLogs: () => void
}) {
  const { basepath } = useRouter()
  return (
    <div className="rtitle">
      <Link to={buildHref(basepath, "/")} className="back">
        ←
      </Link>
      <span className="mono muted">#{cohorte.id}</span>
      <h1 className="mono">{cohorte.identifiant_action}</h1>
      <span className="muted">exécution du {cohorte.execution_datetime}</span>
      <span className="type-tag" title={`Valeur stockée : ${cohorte.type_action}`}>
        {TYPE_ACTIONS[cohorte.type_action] ?? cohorte.type_action_label}
      </span>
      <CohorteStatutPill statut={cohorte.statut} />
      <span className="spacer" />
      <LogsButton cohorteId={cohorte.id} logs={cohorte.logs} onOpen={onOpenLogs} />
    </div>
  )
}

/** Counters of the unit of the view, on the current filters, all statuts. */
export function Counters({ stats, vue }: { stats: Stats; vue: Vue }) {
  const counts = stats.compteurs
  const total = totalOf(counts)
  const decided = total ? Math.round(((total - counts.AVALIDER) / total) * 100) : 0
  return (
    <div className="rtitle">
      <span
        className="tlabel"
        title="Compté sur les filtres en cours, quelle que soit l’option Afficher"
      >
        {vue === "groupes" ? "Groupes" : "Lignes"} du filtre
      </span>
      <div className="counters">
        {STATUT_ORDER.filter((s) => counts[s] || ALWAYS_SHOWN.includes(s)).map((s) => (
          <span key={s} className={`counter p-${STATUTS[s].tone}`}>
            {STATUTS[s].label}
            <b>{formatNumber(counts[s])}</b>
          </span>
        ))}
      </div>
      <div className="progress">
        <StackBar counts={counts} />
        <span className="pct">
          {decided} % décidés · {formatNumber(counts.AVALIDER)} restant
          {counts.AVALIDER > 1 ? "s" : ""}
        </span>
      </div>
    </div>
  )
}
