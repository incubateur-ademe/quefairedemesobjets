import { isActive } from "../../api/masse"
import type { Tache } from "../../api/types"
import { Pill } from "../../components/common/Pill"
import { formatDateTime, plural } from "../../domain/format"
import type { Tone } from "../../domain/statuts"
import { WaButton, WaDrawer, WaSpinner, WaTooltip } from "../../wa"

const STATUTS: Record<Tache["statut"], { label: string; tone: Tone }> = {
  pending: { label: "En attente", tone: "warn" },
  running: { label: "En cours", tone: "info" },
  done: { label: "Terminée", tone: "ok" },
  error: { label: "Erreur", tone: "danger" },
}

const ACTIONS: Record<Tache["action"], string> = {
  report_correction: "Report vers la correction",
  report_parent: "Report vers le parent",
  restore_correction: "Correction avec la valeur initiale",
}

/** Number of tasks of the cohorte, and of those still pending or running. */
export function TachesButton({
  taches,
  onOpen,
}: {
  taches: Tache[]
  onOpen: () => void
}) {
  const active = taches.filter(isActive).length
  const errors = taches.filter((tache) => tache.statut === "error").length
  const detail =
    [
      active && `${active} en cours`,
      errors && `${errors} en erreur`,
      taches.length - active - errors &&
        plural(taches.length - active - errors, "terminée", "terminées"),
    ]
      .filter(Boolean)
      .join(" · ") || "aucune tâche"
  return (
    <>
      <WaButton
        id="taches"
        size="small"
        appearance="outlined"
        variant={active ? "brand" : errors ? "danger" : "neutral"}
        className="taches-btn"
        onClick={onOpen}
      >
        {active > 0 && <WaSpinner slot="start" />}
        Tâches <span className="mono">{taches.length}</span>
        {active > 0 && <span className="taches-active">· {active} en cours</span>}
      </WaButton>
      <WaTooltip for="taches">{detail}</WaTooltip>
    </>
  )
}

/** Side panel listing the background tasks of a cohorte; refreshed (by
 * useTaches) while one is pending or running. */
export function TachesDrawer({
  cohorteId,
  taches,
  open,
  onClose,
}: {
  cohorteId: number
  taches: Tache[] | undefined
  open: boolean
  onClose: () => void
}) {
  return (
    <WaDrawer
      open={open}
      label={`Tâches de la cohorte #${cohorteId}`}
      placement="end"
      className="logs-drawer"
      onWaAfterHide={onClose}
    >
      {taches?.some(isActive) && (
        <p className="muted">
          <WaSpinner /> Mise à jour automatique tant qu’une tâche est en cours
        </p>
      )}
      {taches && (
        <table className="tbl">
          <thead>
            <tr>
              <th>Lancée</th>
              <th>Action</th>
              <th>Groupes</th>
              <th>Statut</th>
              <th>Résultat</th>
            </tr>
          </thead>
          <tbody>
            {taches.map((tache) => (
              <tr key={tache.id}>
                <td>
                  {formatDateTime(tache.lancee_le)}
                  {tache.par && <span className="sub">par {tache.par}</span>}
                </td>
                <td>{ACTIONS[tache.action]}</td>
                <td className="mono">{tache.groupes}</td>
                <td>
                  <Pill tone={STATUTS[tache.statut].tone}>
                    {STATUTS[tache.statut].label}
                  </Pill>
                  {tache.debut && (
                    <span className="sub">début {formatDateTime(tache.debut)}</span>
                  )}
                  {tache.fin && (
                    <span className="sub">fin {formatDateTime(tache.fin)}</span>
                  )}
                </td>
                <td>
                  {tache.statut === "done" &&
                    plural(tache.affected ?? 0, "groupe modifié", "groupes modifiés")}
                  {tache.statut === "error" && (
                    <span className="mono">{tache.erreur || "erreur"}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {taches && !taches.length && <p className="muted">Aucune tâche.</p>}
    </WaDrawer>
  )
}
