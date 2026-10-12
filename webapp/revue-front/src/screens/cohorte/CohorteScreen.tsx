import { useEffect, useMemo, useState } from "react"

import { useGroupeActions } from "../../api/mutations"
import {
  useCohorte,
  useGroupesPage,
  useReviewFilterFields,
  useStats,
  type RevueParams,
} from "../../api/queries"
import type { Groupe } from "../../api/types"
import { LogsDrawer } from "../../components/common/LogsDrawer"
import { Pager, PageSizeSelect } from "../../components/common/Pager"
import { Segmented } from "../../components/common/Segmented"
import { ShortcutsHelp, type Shortcut } from "../../components/common/ShortcutsHelp"
import { FilterBuilder } from "../../components/filters/FilterBuilder"
import {
  countConditions,
  parseFilterParam,
  serializeFilter,
} from "../../domain/filterModel"
import { formatNumber } from "../../domain/format"
import { scrollRowIntoView } from "../../domain/scroll"
import { useSearchParams } from "../../router"
import { WaButton, WaSpinner } from "../../wa"
import { GroupeModal } from "../groupe-modal/GroupeModal"
import { CohorteHeader, Counters } from "./CohorteHeader"
import { cursorItems, groupeCursor, GroupesView, type ModalTab } from "./GroupesView"
import { PAGE_SIZES, readReviewState, TUPLES_SEPARATOR } from "./searchState"
import { TuplesBar } from "./TuplesBar"

const FILTER_HINT =
  "Mêmes filtres dans les deux vues. En vue Groupes, une condition sur la ligne retient les groupes dont au moins une ligne la vérifie ; en vue Lignes, une condition sur le groupe retient les lignes dont le groupe la vérifie."

const SHORTCUTS: Shortcut[] = [
  {
    keys: ["↑", "↓"],
    label: "en-tête du groupe → ses lignes → groupe suivant (et page voisine)",
  },
  {
    keys: ["A"],
    label: "valider l’élément courant (groupe ou ligne), puis passer au suivant",
  },
  { keys: ["R"], label: "refuser le groupe courant" },
  {
    keys: ["U"],
    label:
      "remettre à valider l’élément courant (une ligne d’un groupe refusé rouvre le groupe)",
  },
  { keys: ["⏎"], label: "ouvrir le détail du groupe courant" },
  { keys: ["/"], label: "filtres avancés" },
  { keys: ["Échap"], label: "fermer le détail ou les filtres, annuler une correction" },
]

const isTyping = (target: EventTarget | null) =>
  target instanceof HTMLElement &&
  Boolean(
    target.closest(
      "input, select, textarea, wa-input, wa-select, wa-drawer, wa-dialog, form",
    ),
  )

/** Screen 2: review of a cohorte. */
export function CohorteScreen({ cohorteId }: { cohorteId: number }) {
  const [search, setSearch] = useSearchParams()
  const state = readReviewState(search)
  const [filtersOpen, setFiltersOpen] = useState(Boolean(state.filtre))
  const filter = useMemo(() => parseFilterParam(state.filtre), [state.filtre])

  const revueParams: RevueParams = {
    filtre: state.filtre,
    tuples: state.tuples.length ? state.tuples : undefined,
    afficher: state.afficher,
  }
  const cohorte = useCohorte(cohorteId)
  const fields = useReviewFilterFields(cohorteId)
  const stats = useStats(cohorteId, { ...revueParams, vue: state.vue })
  const groupes = useGroupesPage(cohorteId, {
    ...revueParams,
    page: state.page,
    page_size: state.pageSize,
  })
  const actions = useGroupeActions(cohorteId)
  const items = useMemo(() => groupes.data?.items ?? [], [groupes.data])

  // A change of the list (view, filters, tuples, « afficher », page) resets the page
  const setListSearch = (patch: Record<string, string | undefined>) =>
    setSearch({ ...patch, page: undefined })

  const cursor = useCursor(
    items,
    state.page,
    groupes.data?.total ?? 0,
    state.pageSize,
    (page) => setSearch({ page: String(page) }),
  )

  const modalGroupeId = search.groupe ? Number(search.groupe) : null
  const modalTab = (search.onglet as ModalTab) || "localisation"
  const openModal = (groupe: Groupe, tab: ModalTab) =>
    setSearch({
      groupe: String(groupe.id),
      onglet: tab === "localisation" ? undefined : tab,
    })

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (
        event.metaKey ||
        event.ctrlKey ||
        event.altKey ||
        modalGroupeId !== null ||
        isTyping(event.target)
      ) {
        return
      }
      const key = event.key.toLowerCase()
      if (key === "arrowdown" || key === "arrowup") {
        event.preventDefault()
        cursor.move(key === "arrowdown" ? 1 : -1)
      } else if (key === "a") {
        validateAtCursor(cursor, actions)
      } else if (key === "u") {
        resubmitAtCursor(cursor, actions)
      } else if (key === "r") {
        const groupe = cursor.groupe()
        if (groupe?.capacites.refuser) {
          actions.decideGroupe(groupe, "reject").catch(() => {})
          cursor.nextGroupe()
        }
      } else if (key === "enter") {
        const groupe = cursor.groupe()
        if (groupe) {
          openModal(groupe, "localisation")
        }
      } else if (event.key === "/") {
        event.preventDefault()
        setFiltersOpen(true)
      } else if (key === "escape") {
        setFiltersOpen(false)
      }
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  })

  if (cohorte.error) {
    return <p className="error">{cohorte.error.message}</p>
  }
  if (!cohorte.data) {
    return <WaSpinner />
  }
  const nbConditions = countConditions(filter)
  const totaux = stats.data?.totaux_vues

  return (
    <main className="review">
      <div className="rhead">
        <CohorteHeader
          cohorte={cohorte.data}
          onOpenLogs={() => setSearch({ logs: String(cohorteId) })}
        />
        {stats.data && <Counters stats={stats.data} vue={state.vue} />}
        <div className="rtitle">
          <Segmented
            label="Vue"
            value={state.vue}
            options={[
              { value: "groupes", label: "Groupes", count: totaux?.groupes },
              { value: "lignes", label: "Lignes", count: totaux?.lignes },
            ]}
            onChange={(vue) => setListSearch({ vue, par_page: undefined })}
          />
          <Segmented
            label="Afficher"
            value={state.afficher}
            options={[
              { value: "avalider", label: "À valider uniquement" },
              { value: "tout", label: "Tout" },
            ]}
            onChange={(afficher) => setListSearch({ afficher })}
          />
          <WaButton
            size="small"
            appearance="outlined"
            aria-expanded={filtersOpen}
            onClick={() => setFiltersOpen((open) => !open)}
          >
            Filtres avancés{" "}
            {nbConditions > 0 && <span className="badge">{nbConditions}</span>}{" "}
            <kbd>/</kbd>
          </WaButton>
          <PageSizeSelect
            unit={state.vue}
            sizes={PAGE_SIZES[state.vue]}
            value={state.pageSize}
            onChange={(size) => setListSearch({ par_page: String(size) })}
          />
          <span className="spacer" />
          {(groupes.isFetching || stats.isFetching) && <WaSpinner />}
        </div>
      </div>
      {filtersOpen && fields.data && (
        <div className="fbwrap">
          <FilterBuilder
            fields={fields.data}
            value={filter}
            hint={FILTER_HINT}
            onApply={(next) => setListSearch({ filtre: serializeFilter(next) })}
          />
        </div>
      )}
      <TuplesBar
        stats={stats.data}
        vue={state.vue}
        selected={state.tuples}
        onChange={(tuples) =>
          setListSearch({ tuples: tuples.join(TUPLES_SEPARATOR) || undefined })
        }
      />
      {groupes.error && <p className="error">{groupes.error.message}</p>}
      <div className="scroll grow">
        {state.vue === "groupes" ? (
          groupes.data && (
            <GroupesView
              groupes={items}
              policy={cohorte.data.policy}
              actions={actions}
              cursor={cursor.current}
              onCursor={cursor.set}
              onOpen={openModal}
            />
          )
        ) : (
          <div className="emptystate">
            <b>Vue par lignes</b>
            Bientôt disponible.
          </div>
        )}
      </div>
      <div className="tfoot">
        <ShortcutsHelp id="shortcuts-revue" shortcuts={SHORTCUTS} />
        <span className="spacer" />
        {groupes.data && (
          <Pager
            unit="groupes"
            page={state.page}
            pageSize={state.pageSize}
            total={groupes.data.total}
            onPage={(page) => setSearch({ page: String(page) })}
          />
        )}
        {groupes.data && (
          <span className="muted">{formatNumber(groupes.data.total)} au total</span>
        )}
      </div>
      <GroupeModal
        groupeId={modalGroupeId}
        tab={modalTab}
        policy={cohorte.data.policy}
        actions={actions}
        onTab={(tab) =>
          setSearch(
            { onglet: tab === "localisation" ? undefined : tab },
            { replace: true },
          )
        }
        onClose={() => setSearch({ groupe: undefined, onglet: undefined })}
      />
      <LogsDrawer
        cohorteId={search.logs ? cohorteId : null}
        onClose={() => setSearch({ logs: undefined })}
      />
    </main>
  )
}

type Cursor = ReturnType<typeof useCursor>

/** Single keyboard cursor over the page: groupe headers and lignes. At an end of
 * the page, moves to the neighbour page. */
function useCursor(
  groupes: Groupe[],
  page: number,
  total: number,
  pageSize: number,
  goToPage: (page: number) => void,
) {
  const positions = useMemo(() => cursorItems(groupes), [groupes])
  const [state, setState] = useState<{
    value: string | null
    atEnd?: "first" | "last"
  }>({
    value: null,
  })
  // After a page change, the cursor goes to the first or last position
  let current = state.value && positions.includes(state.value) ? state.value : null
  if (!current && positions.length) {
    current = state.atEnd === "last" ? positions[positions.length - 1] : positions[0]
  }

  useEffect(() => {
    if (current) {
      scrollRowIntoView(
        document.querySelector(`[data-cursor="${current.replace(/"/g, '\\"')}"]`),
      )
    }
  }, [current])

  const set = (value: string) => setState({ value })
  const move = (delta: 1 | -1) => {
    const index = current ? positions.indexOf(current) : -1
    const next = index + delta
    if (next >= 0 && next < positions.length) {
      set(positions[next])
    } else if (delta > 0 && page * pageSize < total) {
      setState({ value: null, atEnd: "first" })
      goToPage(page + 1)
    } else if (delta < 0 && page > 1) {
      setState({ value: null, atEnd: "last" })
      goToPage(page - 1)
    }
  }
  const groupe = () => {
    const index = current ? positions.indexOf(current) : -1
    for (let i = index; i >= 0; i--) {
      if (positions[i].startsWith("g:")) {
        return groupes.find((g) => groupeCursor(g) === positions[i])
      }
    }
    return undefined
  }
  const nextGroupe = () => {
    const index = current ? positions.indexOf(current) : -1
    const next = positions.findIndex(
      (position, i) => i > index && position.startsWith("g:"),
    )
    if (next >= 0) {
      set(positions[next])
    } else {
      move(1)
    }
  }
  return { current, set, move, groupe, nextGroupe }
}

/** « A »: validates the groupe or the ligne under the cursor, then moves on. */
function validateAtCursor(
  cursor: Cursor,
  actions: ReturnType<typeof useGroupeActions>,
) {
  const groupe = cursor.groupe()
  if (!groupe || !cursor.current) {
    return
  }
  if (cursor.current.startsWith("g:")) {
    if (groupe.capacites.valider) {
      actions.decideGroupe(groupe, "validate").catch(() => {})
      cursor.nextGroupe()
    }
    return
  }
  const key = cursor.current.slice(2)
  const ligne = groupe.lignes.find((l) => l.key === key)
  if (ligne?.capacites.valider) {
    actions.decideLignes(groupe, [key], "validate").catch(() => {})
    cursor.move(1)
  }
}

/** « U »: puts back to validate the groupe or the ligne under the cursor. The
 * cursor stays in place, to decide again. */
function resubmitAtCursor(
  cursor: Cursor,
  actions: ReturnType<typeof useGroupeActions>,
) {
  const groupe = cursor.groupe()
  if (!groupe || !cursor.current) {
    return
  }
  if (cursor.current.startsWith("g:")) {
    if (groupe.capacites.remettre_a_valider) {
      actions.decideGroupe(groupe, "resubmit").catch(() => {})
    }
    return
  }
  const key = cursor.current.slice(2)
  const ligne = groupe.lignes.find((l) => l.key === key)
  if (
    ligne?.capacites.remettre_a_valider ||
    ligne?.capacites.remettre_groupe_a_valider
  ) {
    actions.decideLignes(groupe, [key], "resubmit").catch(() => {})
  }
}
