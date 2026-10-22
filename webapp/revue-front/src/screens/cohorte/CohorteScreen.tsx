import { useEffect, useMemo, useState } from "react"

import { useMassAction, useMassPreview } from "../../api/masse"
import { useGroupeActions } from "../../api/mutations"
import {
  useCohorte,
  useGroupesPage,
  useLignesPage,
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
import { scrollRowIntoView, scrollRowToTop } from "../../domain/scroll"
import { useSearchParams } from "../../router"
import {
  emptySelection,
  isSelected,
  pageFullySelected,
  selectedCount,
  selectFilter,
  toggle,
  togglePage,
  type ListFilter,
  type Selection,
} from "../../state/selection"
import { WaButton, WaSpinner } from "../../wa"
import { GroupeModal } from "../groupe-modal/GroupeModal"
import { CohorteHeader } from "./CohorteHeader"
import { cursorItems, GroupesView, ligneCursor, type ModalTab } from "./GroupesView"
import { LignesView } from "./LignesView"
import { MassBar } from "./MassBar"
import { PAGE_SIZES, readReviewState, TUPLES_SEPARATOR } from "./searchState"
import { TachesDrawer } from "./Taches"
import { TuplesBar } from "./TuplesBar"

const FILTER_HINT =
  "Mêmes filtres dans les deux vues. En vue Groupes, une condition sur la ligne retient les groupes dont au moins une ligne la vérifie ; en vue Lignes, une condition sur le groupe retient les lignes dont le groupe la vérifie."

const SHORTCUTS: Shortcut[] = [
  {
    keys: ["↑", "↓"],
    label:
      "élément suivant ou précédent : en-tête du groupe → ses lignes → groupe suivant ; ligne suivante en vue Lignes (et page voisine)",
  },
  {
    keys: ["A"],
    label: "valider l’élément courant (groupe ou ligne), puis passer au suivant",
  },
  {
    keys: ["R"],
    label: "refuser le groupe courant (vue Groupes ; en vue Lignes, depuis le détail)",
  },
  {
    keys: ["U"],
    label:
      "remettre à valider l’élément courant (une ligne d’un groupe refusé rouvre le groupe)",
  },
  { keys: ["X"], label: "cocher ou décocher l’élément courant (actions de masse)" },
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
  const pageParams = { ...revueParams, page: state.page, page_size: state.pageSize }
  const groupes = useGroupesPage(cohorteId, pageParams, state.vue === "groupes")
  const lignes = useLignesPage(cohorteId, pageParams, state.vue === "lignes")
  const current = state.vue === "groupes" ? groupes : lignes
  const actions = useGroupeActions(cohorteId)
  // Groupes of the page, and cursor positions: groupe headers and their lignes, or
  // the lignes of the page
  const pageGroupes = useMemo(
    () => (state.vue === "groupes" ? groupes.data?.items : lignes.data?.groupes) ?? [],
    [state.vue, groupes.data, lignes.data],
  )
  // Groupes as shown: without their lignes already validated, if asked
  const shownGroupes = useMemo(
    () =>
      state.vue === "groupes" && state.masquerValidees
        ? pageGroupes.map((groupe) => ({
            ...groupe,
            lignes: groupe.lignes.filter((ligne) => ligne.statut !== "ATRAITER"),
          }))
        : pageGroupes,
    [state.vue, state.masquerValidees, pageGroupes],
  )
  const positions = useMemo(
    () =>
      state.vue === "groupes"
        ? cursorItems(shownGroupes)
        : (lignes.data?.items ?? []).map((item) => ligneCursor(item.key)),
    [state.vue, shownGroupes, lignes.data],
  )

  // A change of the list (view, filters, tuples, « afficher », page) resets the page
  const setListSearch = (patch: Record<string, string | undefined>) =>
    setSearch({ ...patch, page: undefined })

  // Selection, reset when the list changes (view, filters, tuples, « afficher »)
  const listFilter: ListFilter = revueParams
  const listKey = JSON.stringify({ vue: state.vue, ...revueParams })
  const [selectionState, setSelectionState] = useState<{
    list: string
    selection: Selection
  }>({ list: listKey, selection: emptySelection() })
  const selection =
    selectionState.list === listKey ? selectionState.selection : emptySelection()
  const setSelection = (update: (current: Selection) => Selection) =>
    setSelectionState({ list: listKey, selection: update(selection) })
  const pageIds = useMemo(
    () =>
      state.vue === "groupes"
        ? pageGroupes.map((g) => String(g.id))
        : (lignes.data?.items ?? []).map((item) => item.key),
    [state.vue, pageGroupes, lignes.data],
  )
  const total = current.data?.total ?? 0
  const count = selectedCount(selection, total)
  const preview = useMassPreview(cohorteId, state.vue, selection, listFilter, count > 0)
  const massAction = useMassAction(cohorteId)
  const taches = useTaches(
    cohorteId,
    pageGroupes.map((g) => g.id),
  )
  const checkboxes = {
    isChecked: (id: string) => isSelected(selection, id),
    onToggle: (id: string) => setSelection((current) => toggle(current, id)),
    pageChecked: pageFullySelected(selection, pageIds),
    onTogglePage: (checked: boolean) =>
      setSelection((current) => togglePage(current, pageIds, checked)),
  }

  const cursor = useCursor(
    positions,
    pageGroupes,
    state.page,
    current.data?.total ?? 0,
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
      } else if (key === "x") {
        // Checks the element under the cursor: the groupe, or the ligne (view Lignes)
        const groupe = cursor.groupe()
        const id =
          state.vue === "groupes"
            ? groupe
              ? String(groupe.id)
              : null
            : cursor.current?.slice(2)
        if (id) {
          checkboxes.onToggle(id)
        }
      } else if (key === "u") {
        resubmitAtCursor(cursor, actions)
      } else if (key === "r" && state.vue === "groupes") {
        const groupe = cursor.groupe()
        if (groupe?.capacites.refuser) {
          actions.decideGroupe(groupe, "reject").catch(() => {})
          cursor.nextGroupe(true)
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
          stats={stats.data}
          vue={state.vue}
          taches={taches.data}
          onOpenLogs={() => setSearch({ logs: String(cohorteId) })}
          onOpenTaches={() => {
            setSearch({ taches: "1" })
            taches.refetch()
          }}
        />
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
          {state.vue === "groupes" && (
            <label className="hide-validated">
              <input
                type="checkbox"
                checked={state.masquerValidees}
                onChange={(event) =>
                  setSearch(
                    { masquer_validees: event.target.checked ? "1" : undefined },
                    { replace: true },
                  )
                }
              />
              Masquer les lignes déjà validées
            </label>
          )}
          <PageSizeSelect
            unit={state.vue}
            sizes={PAGE_SIZES[state.vue]}
            value={state.pageSize}
            onChange={(size) => setListSearch({ par_page: String(size) })}
          />
          <span className="spacer" />
          {(current.isFetching || stats.isFetching) && <WaSpinner />}
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
      {count > 0 && (
        <MassBar
          vue={state.vue}
          policy={cohorte.data.policy}
          count={count}
          total={total}
          filterMode={selection.mode === "filtre"}
          canSelectFilter={
            selection.mode === "page" &&
            pageFullySelected(selection, pageIds) &&
            total > selection.ids.size
          }
          counts={preview.data}
          loadingCounts={preview.isFetching}
          running={massAction.isPending}
          onSelectFilter={() => setSelection(() => selectFilter())}
          onClear={() => setSelection(() => emptySelection())}
          onRun={(action) =>
            massAction
              .mutateAsync({
                vue: state.vue,
                action,
                selection,
                list: listFilter,
                pageGroupeIds: pageGroupes.map((g) => g.id),
              })
              .then(() => setSelection(() => emptySelection()))
              .catch(() => {})
          }
        />
      )}
      {current.error && <p className="error">{current.error.message}</p>}
      <div className="scroll grow">
        {state.vue === "groupes"
          ? groupes.data && (
              <GroupesView
                groupes={shownGroupes}
                policy={cohorte.data.policy}
                actions={actions}
                cursor={cursor.current}
                onCursor={cursor.set}
                onOpen={openModal}
                checkboxes={checkboxes}
              />
            )
          : lignes.data && (
              <LignesView
                page={lignes.data}
                actions={actions}
                cursor={cursor.current}
                onCursor={cursor.set}
                onOpen={openModal}
                checkboxes={checkboxes}
              />
            )}
      </div>
      <div className="tfoot">
        <ShortcutsHelp id="shortcuts-revue" shortcuts={SHORTCUTS} />
        <span className="spacer" />
        {current.data && (
          <Pager
            unit={state.vue}
            page={state.page}
            pageSize={state.pageSize}
            total={current.data.total}
            onPage={(page) => setSearch({ page: String(page) })}
          />
        )}
        {current.data && (
          <span className="muted">{formatNumber(current.data.total)} au total</span>
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
      <TachesDrawer
        cohorteId={cohorteId}
        taches={taches.data}
        open={Boolean(search.taches)}
        onClose={() => setSearch({ taches: undefined })}
      />
    </main>
  )
}

type Cursor = ReturnType<typeof useCursor>

/** Single keyboard cursor over the page: groupe headers and lignes. At an end of
 * the page, moves to the neighbour page. After a decision (`toTop`), the next
 * position is smoothly scrolled to the top of the table. */
function useCursor(
  positions: string[],
  groupes: Groupe[],
  page: number,
  total: number,
  pageSize: number,
  goToPage: (page: number) => void,
) {
  const [state, setState] = useState<{
    value: string | null
    atEnd?: "first" | "last"
    toTop?: boolean
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
      const rows = document.querySelectorAll<HTMLElement>("[data-cursor]")
      const row = Array.from(rows).find((row) => row.dataset.cursor === current) ?? null
      if (state.toTop) {
        scrollRowToTop(row)
      } else {
        scrollRowIntoView(row)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- scrolls on moves only
  }, [current])

  const set = (value: string, toTop = false) => setState({ value, toTop })
  const move = (delta: 1 | -1, toTop = false) => {
    const index = current ? positions.indexOf(current) : -1
    const next = index + delta
    if (next >= 0 && next < positions.length) {
      set(positions[next], toTop)
    } else if (delta > 0 && page * pageSize < total) {
      setState({ value: null, atEnd: "first", toTop })
      goToPage(page + 1)
    } else if (delta < 0 && page > 1) {
      setState({ value: null, atEnd: "last", toTop })
      goToPage(page - 1)
    }
  }
  /** Groupe of the position: « g:<id> » or « l:<id>:<champs> ». */
  const groupe = () => {
    const id = current ? Number(current.split(":")[1]) : NaN
    return groupes.find((g) => g.id === id)
  }
  const nextGroupe = (toTop = false) => {
    const index = current ? positions.indexOf(current) : -1
    const next = positions.findIndex(
      (position, i) => i > index && position.startsWith("g:"),
    )
    if (next >= 0) {
      set(positions[next], toTop)
    } else {
      move(1, toTop)
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
      cursor.nextGroupe(true)
    }
    return
  }
  const key = cursor.current.slice(2)
  const ligne = groupe.lignes.find((l) => l.key === key)
  if (ligne?.capacites.valider) {
    actions.decideLignes(groupe, [key], "validate").catch(() => {})
    cursor.move(1, true)
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
