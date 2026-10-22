import type { GroupeActions } from "../../api/mutations"
import type { Groupe, Ligne, Modele, Policy } from "../../api/types"
import { StatutPill } from "../../components/common/Pill"
import { plural } from "../../domain/format"
import { WaButton } from "../../wa"
import {
  ActeurCell,
  ChampsCell,
  Decided,
  LigneActionCell,
  ReportButton,
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

export function LigneHead() {
  return (
    <>
      <th>Champ(s)</th>
      <th>
        Acteur importé
        <span className="hsub">suggestion de la source, non corrigeable</span>
      </th>
      <th className="c-rep" title="Reporter vers la correction">
        ▶
      </th>
      <th>
        Correction<span className="hsub">RevisionActeur · corrigeable</span>
      </th>
      <th className="c-rep" title="Reporter vers le parent">
        ⏩
      </th>
      <th>
        Parent<span className="hsub">ParentRevisionActeur · corrigeable</span>
      </th>
      <th>Statut</th>
      <th />
    </>
  )
}

const PROCESSING = ["ENCOURS", "SUCCES", "ERREUR"]

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

export type ModalTab = "localisation" | "annuaire"

const MODAL_TABS: [ModalTab, string][] = [
  ["localisation", "Localisation"],
  ["annuaire", "Annuaire entreprise"],
]

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
          <span className="gname">{acteur.nom || "—"}</span>
          {groupe.is_new && policy.badge && (
            <span className="pill p-accent">{policy.badge}</span>
          )}
        </div>
        <div className="gmeta">
          <span className="mono faint">{acteur.identifiant_unique}</span>
          <span className="muted">{acteur.ville}</span>
        </div>
        <div className="gmeta">
          {MODAL_TABS.map(([tab, label]) => (
            <WaButton
              key={tab}
              size="small"
              appearance="plain"
              onClick={(event) => {
                event.stopPropagation()
                onOpen(groupe, tab)
              }}
            >
              {label}
            </WaButton>
          ))}
        </div>
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
        <ReportAll groupe={groupe} modele="RevisionActeur" actions={actions} />
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
          <span className="inherit">pas de correction existante</span>
        )}
      </td>
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
          <span className="inherit">pas de parent</span>
        )}
      </td>
      <td>
        <StatutPill statut={groupe.statut} />
        <Decided par={groupe.decision_par} le={groupe.decision_le} />
        <div className="lineprog">
          <span className="stack">
            <span
              className="bg-ok"
              style={{
                width: `${groupe.lignes_total ? (groupe.lignes_validees / groupe.lignes_total) * 100 : 0}%`,
              }}
            />
          </span>
          {groupe.lignes_validees}/{groupe.lignes_total} lignes
        </div>
      </td>
      <td>
        <div className="gact">
          <GroupeActionsButtons groupe={groupe} actions={actions} />
        </div>
      </td>
    </tr>
  )
}

/** A ligne de suggestion: one row of the comparison table, as in the admin. */
export function LigneRow({
  groupe,
  ligne,
  actions,
  cursor,
  onCursor,
  lead,
}: {
  groupe: Groupe
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
        <ReportButton
          groupe={groupe}
          ligne={ligne}
          modele="RevisionActeur"
          actions={actions}
        />
      </td>
      <td className="c-tgt">
        <TargetCell
          groupe={groupe}
          ligne={ligne}
          modele="RevisionActeur"
          actions={actions}
        />
      </td>
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
      <td>
        <StatutCell ligne={ligne} />
      </td>
      <td>
        <LigneActionCell groupe={groupe} ligne={ligne} actions={actions} />
      </td>
    </tr>
  )
}

/** Decision buttons of a groupe (header row and modal). */
export function GroupeActionsButtons({
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
    <table className="tbl cmp stream">
      <thead>
        <tr>
          <PageCheckbox
            label="Sélectionner les groupes de cette page"
            checkboxes={checkboxes}
          />
          <LigneHead />
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
