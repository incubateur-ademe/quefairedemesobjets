import type { GroupeActions } from "../../api/mutations"
import type { Groupe, LignePage, Policy } from "../../api/types"
import {
  type Checkboxes,
  cmpTableClass,
  ligneCursor,
  LigneHead,
  LigneRow,
  type ModalTab,
  PageCheckbox,
  RowCheckbox,
} from "./GroupesView"

/** View « Lignes » (focus mode): one row per ligne de suggestion, with its groupe
 * and acteur for context. A ligne is refused here only when the policy allows it
 * (lignes decided one by one); otherwise a refusal is a decision on the whole
 * groupe, taken from the detail of the groupe. */
export function LignesView({
  page,
  policy,
  actions,
  cursor,
  onCursor,
  onOpen,
  checkboxes,
}: {
  page: LignePage
  policy: Policy
  actions: GroupeActions
  cursor: string | null
  onCursor: (cursor: string) => void
  onOpen: (groupe: Groupe, tab?: ModalTab) => void
  checkboxes: Checkboxes
}) {
  const groupes = new Map(page.groupes.map((groupe) => [groupe.id, groupe]))
  if (!page.items.length) {
    return (
      <div className="emptystate">
        <b>Plus rien à valider ici</b>
        Toutes les lignes de ce filtre sont décidées. Choisissez « Tout » pour les
        revoir.
      </div>
    )
  }
  return (
    <table className={`${cmpTableClass(policy)} lignes`}>
      <thead>
        <tr>
          <PageCheckbox
            label="Sélectionner les lignes de cette page"
            checkboxes={checkboxes}
          />
          <th className="num">Groupe</th>
          <th>Acteur</th>
          <LigneHead policy={policy} />
        </tr>
      </thead>
      <tbody>
        {page.items.map((item) => {
          const groupe = groupes.get(item.groupe_id)
          const ligne = groupe?.lignes.find((l) => l.key === item.key)
          if (!groupe || !ligne) {
            return null
          }
          return (
            <LigneRow
              key={item.key}
              groupe={groupe}
              policy={policy}
              ligne={ligne}
              actions={actions}
              cursor={cursor}
              onCursor={onCursor}
              lead={
                <>
                  <RowCheckbox
                    id={ligne.key}
                    label={`Sélectionner la ligne ${ligne.champs.join(", ")} du groupe ${groupe.id}`}
                    checkboxes={checkboxes}
                  />
                  <td className="num">
                    {policy.tabs.length > 0 ? (
                      <button
                        type="button"
                        className="lk mono"
                        title="Détail du groupe"
                        onClick={(event) => {
                          event.stopPropagation()
                          onCursor(ligneCursor(ligne.key))
                          onOpen(groupe)
                        }}
                      >
                        {groupe.id}
                      </button>
                    ) : (
                      <span className="mono">{groupe.id}</span>
                    )}
                  </td>
                  <td>
                    <span className="nom">
                      {ligne.target?.nom || groupe.acteur.nom || "—"}
                    </span>
                    <span className="sub">
                      {ligne.target?.identifiant_unique ??
                        groupe.acteur.identifiant_unique}
                    </span>
                  </td>
                </>
              }
            />
          )
        })}
      </tbody>
    </table>
  )
}
