import type { CohorteDetail, Stats, Vue } from "../../api/types"
import { LogsButton } from "../../components/common/LogsButton"
import { CohorteStatutDot } from "../../components/common/Pill"
import { formatNumber } from "../../domain/format"
import { STATUT_ORDER, STATUTS } from "../../domain/statuts"
import { buildHref, Link, useRouter } from "../../router"

const ALWAYS_SHOWN = ["AVALIDER", "ATRAITER", "REJETEE"]

/** Single line: cohorte, then counters of the unit of the view. */
export function CohorteHeader({
  cohorte,
  stats,
  vue,
  onOpenLogs,
}: {
  cohorte: CohorteDetail
  stats: Stats | undefined
  vue: Vue
  onOpenLogs: () => void
}) {
  const { basepath } = useRouter()
  return (
    <div className="rtitle">
      <Link to={buildHref(basepath, "/")} className="back">
        ←
      </Link>
      <span className="mono muted">#{cohorte.id}</span>
      <CohorteStatutDot statut={cohorte.statut} />
      <h1 className="mono">{cohorte.identifiant_action}</h1>
      <span className="muted">{cohorte.execution_datetime}</span>
      {stats && <Counters stats={stats} vue={vue} />}
      <span className="spacer" />
      <LogsButton cohorteId={cohorte.id} logs={cohorte.logs} onOpen={onOpenLogs} />
    </div>
  )
}

/** Counters of the unit of the view, on the current filters, all statuts. */
function Counters({ stats, vue }: { stats: Stats; vue: Vue }) {
  const counts = stats.compteurs
  return (
    <div
      className="counters"
      title={`${vue === "groupes" ? "Groupes" : "Lignes"} du filtre : comptés sur les filtres en cours, quelle que soit l’option Afficher`}
    >
      {STATUT_ORDER.filter((s) => counts[s] || ALWAYS_SHOWN.includes(s)).map((s) => (
        <span key={s} className={`counter p-${STATUTS[s].tone}`}>
          {STATUTS[s].label}
          <b>{formatNumber(counts[s])}</b>
        </span>
      ))}
    </div>
  )
}
