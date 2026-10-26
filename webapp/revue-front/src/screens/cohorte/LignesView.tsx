import type { GroupeActions } from "../../api/mutations"
import type { Groupe, LignePage } from "../../api/types"
import {
  type Checkboxes,
  type ModalTab,
  LigneHead,
  LigneRow,
  ligneCursor,
  PageCheckbox,
  RowCheckbox,
} from "./GroupesView"

/** View « Lignes » (focus mode): one row per ligne de suggestion, with its groupe
 * and acteur for context. No refusal here: a refusal is a decision on the whole
 * groupe, taken from the detail of the groupe. */
export function LignesView({
  page,
  actions,
  cursor,
  onCursor,
  onOpen,
  checkboxes,
}: {
  page: LignePage
  actions: GroupeActions
  cursor: string | null
  onCursor: (cursor: string) => void
  onOpen: (groupe: Groupe, tab: ModalTab) => void
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
    <table className="tbl cmp stream lignes">
      <thead>
        <tr>
          <PageCheckbox
            label="Sélectionner les lignes de cette page"
            checkboxes={checkboxes}
          />
          <th className="num">Groupe</th>
          <th>Acteur</th>
          <LigneHead />
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
                    <button
                      type="button"
                      className="lk mono"
                      title="Détail du groupe"
                      onClick={(event) => {
                        event.stopPropagation()
                        onCursor(ligneCursor(ligne.key))
                        onOpen(groupe, "localisation")
                      }}
                    >
                      {groupe.id}
                    </button>
                  </td>
                  <td>
                    <span className="nom">{groupe.acteur.nom || "—"}</span>
                    <span className="sub">{groupe.acteur.identifiant_unique}</span>
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
