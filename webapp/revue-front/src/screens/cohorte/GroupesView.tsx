import type { GroupeActions } from "../../api/mutations"
import type { Groupe, Ligne, Modele, Policy } from "../../api/types"
import { StatutPill } from "../../components/common/Pill"
import { plural } from "../../domain/format"
import { WaButton } from "../../wa"
import {
  ActeurCell,
  ChampsCell,
  LigneActionCell,
  ReportButton,
  RestoreButton,
  EmptyButton,
  StatutCell,
  TargetCell,
} from "./cells/LigneCells"

export const groupeCursor = (groupe: Groupe) => `g:${groupe.id}`
export const ligneCursor = (key: string) => `l:${key}`

/** Cursor positions of a page: groupe header, then each of its lignes. */
export function cursorItems(groupes: Groupe[]): string[] {
  return groupes.flatMap((groupe) => [
    groupeCursor(groupe),
    ...groupe.lignes.map((ligne) => ligneCursor(ligne.key)),
  ])
}

export function LigneHead({ policy }: { policy: Policy }) {
  return (
    <>
      <th className="c-champs">Champ(s)</th>
      <th className="c-cmp">
        Acteur importé
        <span className="hsub">suggestion de la source, non corrigeable</span>
      </th>
      <th className="c-rep" title="Reporter vers la correction">
        ▶
      </th>
      <th className="c-cmp">
        Correction<span className="hsub">RevisionActeur · corrigeable</span>
      </th>
      {policy.colonne_parent && (
        <>
          <th className="c-rep" title="Reporter vers le parent">
            ⏩
          </th>
          <th className="c-cmp">
            Parent<span className="hsub">ParentRevisionActeur · corrigeable</span>
          </th>
        </>
      )}
      <th>Statut</th>
      <th />
    </>
  )
}

const PROCESSING = ["ENCOURS", "SUCCES", "ERREUR"]
// Statuts of the groupes showing the progress of their lignes
const WITH_PROGRESS = ["AVALIDER", "ATRAITER"]

/** Correction with the value of the acteur on every restorable ligne. */
function RestoreAll({ groupe, actions }: { groupe: Groupe; actions: GroupeActions }) {
  const count = groupe.lignes.filter(
    (ligne) => ligne.capacites.restore_correction,
  ).length
  if (!count) {
    return null
  }
  return (
    <button
      type="button"
      className="rep all"
      title={`Corriger ${plural(count, "ligne")} avec la valeur initiale`}
      onClick={(event) => {
        event.stopPropagation()
        actions.restore(groupe).catch(() => {})
      }}
    >
      ‹‹
      <small>tout</small>
    </button>
  )
}

/** Correction emptying the value on every ligne of text fields. */
function EmptyAll({ groupe, actions }: { groupe: Groupe; actions: GroupeActions }) {
  const count = groupe.lignes.filter((ligne) => ligne.capacites.empty_correction).length
  if (!count) {
    return null
  }
  return (
    <button
      type="button"
      className="rep all"
      title={`Vider la correction de ${plural(count, "ligne")}`}
      onClick={(event) => {
        event.stopPropagation()
        actions.empty(groupe).catch(() => {})
      }}
    >
      ✕<small>tout</small>
    </button>
  )
}

function ReportAll({
  groupe,
  modele,
  actions,
}: {
  groupe: Groupe
  modele: Modele
  actions: GroupeActions
}) {
  const capacity =
    modele === "RevisionActeur" ? "reporter_correction" : "reporter_parent"
  const count = groupe.lignes.filter((ligne) => ligne.capacites[capacity]).length
  if (!count) {
    return <span className="repoff">·</span>
  }
  return (
    <button
      type="button"
      className="rep all"
      title={`Reporter les ${plural(count, "suggestion")} de l’acteur ${modele === "RevisionActeur" ? "vers la correction" : "vers le parent"}`}
      onClick={(event) => {
        event.stopPropagation()
        actions.report(groupe, modele).catch(() => {})
      }}
    >
      {modele === "RevisionActeur" ? "▶" : "⏩"}
      <small>tout</small>
    </button>
  )
}

export type ModalTab = Policy["tabs"][number]

export const MODAL_TABS: Record<ModalTab, string> = {
  localisation: "Localisation",
  annuaire: "Annuaire entreprise",
}

/** Class of the comparison table: when a groupe gathers several acteurs, the
 * first column (champs and acteur of the ligne) is wider. */
export const cmpTableClass = (policy: Policy) =>
  `tbl cmp stream${policy.lignes_by_acteur ? " by-acteur" : ""}${policy.colonne_parent ? "" : " sans-parent"}`

export type Checkboxes = {
  isChecked: (id: string) => boolean
  onToggle: (id: string) => void
  pageChecked: boolean
  onTogglePage: (checked: boolean) => void
}

export function RowCheckbox({
  id,
  label,
  checkboxes,
}: {
  id: string
  label: string
  checkboxes: Checkboxes
}) {
  return (
    <td className="chk" onClick={(event) => event.stopPropagation()}>
      <input
        type="checkbox"
        aria-label={label}
        checked={checkboxes.isChecked(id)}
        onChange={() => checkboxes.onToggle(id)}
      />
    </td>
  )
}

export function PageCheckbox({
  label,
  checkboxes,
}: {
  label: string
  checkboxes: Checkboxes
}) {
  return (
    <th className="chk">
      <input
        type="checkbox"
        aria-label={label}
        checked={checkboxes.pageChecked}
        onChange={(event) => checkboxes.onTogglePage(event.target.checked)}
      />
    </th>
  )
}

function GroupeHeaderRow({
  groupe,
  policy,
  actions,
  cursor,
  onCursor,
  onOpen,
  checkboxes,
}: {
  groupe: Groupe
  policy: Policy
  actions: GroupeActions
  cursor: string | null
  onCursor: (cursor: string) => void
  onOpen: (groupe: Groupe, tab: ModalTab) => void
  checkboxes: Checkboxes
}) {
  const { acteur } = groupe
  const isCursor = cursor === groupeCursor(groupe)
  return (
    <tr
      className={`ghead st-${groupe.statut}${PROCESSING.includes(groupe.statut) ? " ro" : ""}${isCursor ? " cur" : ""}`}
      data-cursor={groupeCursor(groupe)}
      onClick={() => onCursor(groupeCursor(groupe))}
    >
      <RowCheckbox
        id={String(groupe.id)}
        label={`Sélectionner le groupe ${groupe.id}`}
        checkboxes={checkboxes}
      />
      <td colSpan={2}>
        <div className="gh">
          <span className="mono muted">#{groupe.id}</span>
          <span className="gname">{groupe.libelle || acteur.nom || "—"}</span>
          {groupe.is_new && policy.badge && (
            <span className="pill p-accent">{policy.badge}</span>
          )}
        </div>
        <div className="gmeta">
          <span className="mono faint">{acteur.identifiant_unique}</span>
          <span className="muted">{acteur.ville}</span>
        </div>
        {policy.tabs.length > 0 && (
          <div className="gmeta">
            {policy.tabs.map((tab) => (
              <WaButton
                key={tab}
                size="small"
                appearance="outlined"
                onClick={(event) => {
                  event.stopPropagation()
                  onOpen(groupe, tab)
                }}
              >
                {MODAL_TABS[tab]}
              </WaButton>
            ))}
          </div>
        )}
        <div className="glinks">
          {acteur.admin_urls.importe && (
            <a
              className="lk"
              href={acteur.admin_urls.importe}
              target="_blank"
              rel="noreferrer"
            >
              importé
            </a>
          )}
          {acteur.admin_urls.affiche && (
            <a
              className="lk"
              href={acteur.admin_urls.affiche}
              target="_blank"
              rel="noreferrer"
            >
              affiché
            </a>
          )}
        </div>
      </td>
      <td className="c-rep">
        <div className="reps reps--col">
          <ReportAll groupe={groupe} modele="RevisionActeur" actions={actions} />
          <RestoreAll groupe={groupe} actions={actions} />
          <EmptyAll groupe={groupe} actions={actions} />
        </div>
      </td>
      <td>
        {acteur.admin_urls.corrige ? (
          <div className="glinks">
            <a
              className="lk"
              href={acteur.admin_urls.corrige}
              target="_blank"
              rel="noreferrer"
            >
              corrigé
            </a>
          </div>
        ) : (
          // A groupe of several acteurs has no correction of its own
          !policy.lignes_by_acteur && (
            <span className="inherit">pas de correction existante</span>
          )
        )}
      </td>
      {policy.colonne_parent && (
        <GroupeParentCells groupe={groupe} policy={policy} actions={actions} />
      )}
      <td>
        <StatutPill
          statut={groupe.statut}
          decision={{ par: groupe.decision_par, le: groupe.decision_le }}
        />
        {WITH_PROGRESS.includes(groupe.statut) && <LignesProgress groupe={groupe} />}
      </td>
      <td className="c-act">
        <div className="gact">
          <GroupeActionsButtons groupe={groupe} actions={actions} />
        </div>
      </td>
    </tr>
  )
}

/** Parent cells of a groupe header row: report of all its lignes and links. */
function GroupeParentCells({
  groupe,
  policy,
  actions,
}: {
  groupe: Groupe
  policy: Policy
  actions: GroupeActions
}) {
  const { acteur } = groupe
  return (
    <>
      <td className="c-rep">
        {groupe.parent && (
          <ReportAll groupe={groupe} modele="ParentRevisionActeur" actions={actions} />
        )}
      </td>
      <td>
        {groupe.parent ? (
          <>
            <div className="glinks">
              {acteur.admin_urls.parent && (
                <a
                  className="lk"
                  href={acteur.admin_urls.parent}
                  target="_blank"
                  rel="noreferrer"
                >
                  parent
                </a>
              )}
            </div>
            <span className="decided">
              {plural(groupe.parent.nb_enfants, "enfant impacté", "enfants impactés")}
            </span>
          </>
        ) : (
          // A groupe of several acteurs has no parent of its own
          !policy.lignes_by_acteur && <span className="inherit">pas de parent</span>
        )}
      </td>
    </>
  )
}

/** Progress of the lignes of a groupe to validate or to process: validated (green), refused (red), still
 * to validate (grey, background of the bar), and the count of decided lignes. */
function LignesProgress({ groupe }: { groupe: Groupe }) {
  const { lignes_validees, lignes_refusees, lignes_total } = groupe
  const width = (count: number) => `${lignes_total ? (count / lignes_total) * 100 : 0}%`
  const decided = lignes_validees + lignes_refusees
  return (
    <div
      className="lineprog"
      title={`${plural(lignes_validees, "ligne validée", "lignes validées")}, ${plural(lignes_refusees, "refusée", "refusées")}, ${plural(lignes_total - decided, "à valider", "à valider")}`}
    >
      <span className="stack">
        <span className="bg-ok" style={{ width: width(lignes_validees) }} />
        <span className="bg-danger" style={{ width: width(lignes_refusees) }} />
      </span>
      {decided}/{lignes_total}
    </div>
  )
}

/** A ligne de suggestion: one row of the comparison table, as in the admin. */
export function LigneRow({
  groupe,
  policy,
  ligne,
  actions,
  cursor,
  onCursor,
  lead,
}: {
  groupe: Groupe
  policy: Policy
  ligne: Ligne
  actions: GroupeActions
  cursor?: string | null
  onCursor?: (cursor: string) => void
  /** Cells before the comparison columns (view « Lignes »), else a gutter */
  lead?: React.ReactNode
}) {
  const id = ligneCursor(ligne.key)
  return (
    <tr
      className={`ln st-${ligne.statut}${PROCESSING.includes(ligne.statut) ? " ro" : ""}${cursor === id ? " cur" : ""}`}
      data-cursor={onCursor ? id : undefined}
      onClick={() => onCursor?.(id)}
    >
      {lead ?? <td className="gutter" />}
      <td>
        <ChampsCell ligne={ligne} />
      </td>
      <td className="c-src">
        <ActeurCell ligne={ligne} />
      </td>
      <td className="c-rep">
        <div className="reps">
          <RestoreButton groupe={groupe} ligne={ligne} actions={actions} />
          <EmptyButton groupe={groupe} ligne={ligne} actions={actions} />
          <ReportButton
            groupe={groupe}
            ligne={ligne}
            modele="RevisionActeur"
            actions={actions}
          />
        </div>
      </td>
      <td className="c-tgt">
        <TargetCell
          groupe={groupe}
          ligne={ligne}
          modele="RevisionActeur"
          actions={actions}
        />
      </td>
      {policy.colonne_parent && (
        <>
          <td className="c-rep">
            <ReportButton
              groupe={groupe}
              ligne={ligne}
              modele="ParentRevisionActeur"
              actions={actions}
            />
          </td>
          <td className="c-tgt c-par">
            <TargetCell
              groupe={groupe}
              ligne={ligne}
              modele="ParentRevisionActeur"
              actions={actions}
            />
          </td>
        </>
      )}
      <td>
        <StatutCell ligne={ligne} />
      </td>
      <td className="c-act">
        <LigneActionCell groupe={groupe} ligne={ligne} actions={actions} />
      </td>
    </tr>
  )
}

/** Decision buttons of a groupe header row. */
function GroupeActionsButtons({
  groupe,
  actions,
}: {
  groupe: Groupe
  actions: GroupeActions
}) {
  const decide =
    (action: "validate" | "reject" | "resubmit") => (event: React.MouseEvent) => {
      event.stopPropagation()
      actions.decideGroupe(groupe, action).catch(() => {})
    }
  return (
    <>
      {groupe.capacites.refuser && (
        <WaButton
          size="small"
          variant="danger"
          appearance="outlined"
          onClick={decide("reject")}
        >
          Refuser le groupe
        </WaButton>
      )}
      {groupe.capacites.valider && (
        <WaButton size="small" variant="success" onClick={decide("validate")}>
          Valider le groupe
        </WaButton>
      )}
      {groupe.capacites.remettre_a_valider && (
        <WaButton size="small" appearance="outlined" onClick={decide("resubmit")}>
          Remettre à valider
        </WaButton>
      )}
      {PROCESSING.includes(groupe.statut) && (
        <span className="lock">lecture seule</span>
      )}
    </>
  )
}

/** Flow of groupes: each groupe is shown entirely, its header row being aligned
 * with the columns of its lignes. */
export function GroupesView({
  groupes,
  policy,
  actions,
  cursor,
  onCursor,
  onOpen,
  checkboxes,
}: {
  groupes: Groupe[]
  policy: Policy
  actions: GroupeActions
  cursor: string | null
  onCursor: (cursor: string) => void
  onOpen: (groupe: Groupe, tab: ModalTab) => void
  checkboxes: Checkboxes
}) {
  if (!groupes.length) {
    return (
      <div className="emptystate">
        <b>Plus rien à valider ici</b>
        Tous les groupes de ce filtre sont décidés. Choisissez « Tout » pour les revoir.
      </div>
    )
  }
  return (
    <table className={cmpTableClass(policy)}>
      <thead>
        <tr>
          <PageCheckbox
            label="Sélectionner les groupes de cette page"
            checkboxes={checkboxes}
          />
          <LigneHead policy={policy} />
        </tr>
      </thead>
      {groupes.map((groupe) => (
        <tbody
          key={groupe.id}
          className={`gbody st-${groupe.statut}${cursor === groupeCursor(groupe) ? " gfocus" : ""}`}
        >
          <GroupeHeaderRow
            groupe={groupe}
            policy={policy}
            actions={actions}
            cursor={cursor}
            onCursor={onCursor}
            onOpen={onOpen}
            checkboxes={checkboxes}
          />
          {groupe.lignes.map((ligne) => (
            <LigneRow
              key={ligne.key}
              groupe={groupe}
              policy={policy}
              ligne={ligne}
              actions={actions}
              cursor={cursor}
              onCursor={onCursor}
            />
          ))}
        </tbody>
      ))}
    </table>
  )
}
