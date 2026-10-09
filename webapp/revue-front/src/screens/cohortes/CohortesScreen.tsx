import { useEffect, useMemo, useState } from "react"

import {
  useCohortes,
  useCohortesFilterFields,
  type CohortesParams,
} from "../../api/queries"
import type { Cohorte } from "../../api/types"
import { LogsButton } from "../../components/common/LogsButton"
import { LogsDrawer } from "../../components/common/LogsDrawer"
import { PageSizeSelect, Pager } from "../../components/common/Pager"
import { CohorteStatutPill } from "../../components/common/Pill"
import { Segmented } from "../../components/common/Segmented"
import { StackBar, StatutLegend, totalOf } from "../../components/common/StackBar"
import { FilterBuilder } from "../../components/filters/FilterBuilder"
import { daysAgo, formatDateTime, plural } from "../../domain/format"
import {
  countConditions,
  parseFilterParam,
  serializeFilter,
} from "../../domain/filterModel"
import { TYPE_ACTIONS } from "../../domain/statuts"
import { buildHref, Link, useRouter, useSearchParams } from "../../router"
import { WaButton, WaSpinner } from "../../wa"

const PAGE_SIZES = [25, 50, 100, 200]
const DEFAULT_PAGE_SIZE = 50
const PERIODS = [
  { value: "7", label: "7 jours" },
  { value: "30", label: "30 jours" },
  { value: "", label: "Tout" },
]

type Sort = { key: string; descending: boolean }

const parseSort = (tri: string | undefined): Sort => ({
  key: (tri ?? "-cree_le").replace(/^-/, ""),
  descending: (tri ?? "-cree_le").startsWith("-"),
})

/** Screen 1: SOURCE cohortes having at least one groupe. */
export function CohortesScreen() {
  const { basepath, navigate } = useRouter()
  const [search, setSearch] = useSearchParams()
  const [filtersOpen, setFiltersOpen] = useState(Boolean(search.filtre))
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  // Keyboard focus, reset when the list changes (filters, sort, page)
  const [focusState, setFocusState] = useState({ list: "", index: 0 })

  const filter = useMemo(() => parseFilterParam(search.filtre), [search.filtre])
  const page = Number(search.page) || 1
  const pageSize = Number(search.par_page) || DEFAULT_PAGE_SIZE
  const params: CohortesParams = {
    filtre: serializeFilter(filter),
    type_action: search.type ? [search.type] : undefined,
    statut: search.statut ? [search.statut] : undefined,
    cree_apres: search.periode ? daysAgo(Number(search.periode)) : undefined,
    tri: search.tri,
    page,
    page_size: pageSize,
  }
  const cohortes = useCohortes(params)
  const fields = useCohortesFilterFields()
  const items = cohortes.data?.items ?? []
  const sort = parseSort(search.tri)
  const logsCohorteId = search.logs ? Number(search.logs) : null
  const listKey = JSON.stringify(params)
  const focus = focusState.list === listKey ? focusState.index : 0
  const setFocus = (update: (index: number) => number) =>
    setFocusState({ list: listKey, index: update(focus) })

  // Any change of the list (filter, sort, page) resets the page or the focus
  const setListSearch = (patch: Record<string, string | undefined>) =>
    setSearch({ ...patch, page: undefined })
  const openCohorte = (cohorte: Cohorte) =>
    navigate(buildHref(basepath, `/cohortes/${cohorte.id}`))

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement
      if (target.closest("input, select, textarea, wa-input, wa-select, wa-drawer")) {
        return
      }
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault()
        setFocus((current) =>
          Math.max(
            0,
            Math.min(items.length - 1, current + (event.key === "ArrowDown" ? 1 : -1)),
          ),
        )
      } else if (event.key === "Enter" && items[focus]) {
        openCohorte(items[focus])
      } else if (event.key === "/") {
        event.preventDefault()
        setFiltersOpen(true)
      }
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  })

  const header = (key: string, label: string, className = "") => {
    const active = sort.key === key
    return (
      <th
        className={`sortable ${className}`}
        aria-sort={active ? (sort.descending ? "descending" : "ascending") : "none"}
        onClick={() =>
          setListSearch({ tri: `${active && !sort.descending ? "-" : ""}${key}` })
        }
      >
        {label}
        {active && (sort.descending ? " ▼" : " ▲")}
      </th>
    )
  }

  const nbConditions = countConditions(filter)

  return (
    <main className="screen screen--full">
      <div className="toolbar">
        <Segmented
          label="Type"
          value={search.type ?? ""}
          options={[
            { value: "", label: "Tous" },
            ...Object.entries(TYPE_ACTIONS).map(([value, label]) => ({ value, label })),
          ]}
          onChange={(type) => setListSearch({ type })}
        />
        <Segmented
          label="Statut"
          value={search.statut ?? ""}
          options={[
            { value: "", label: "Tous" },
            { value: "AVALIDER", label: "À valider" },
            { value: "ENCOURS", label: "En cours" },
            { value: "SUCCES", label: "Traitées" },
          ]}
          onChange={(statut) => setListSearch({ statut })}
        />
        <Segmented
          label="Créée"
          value={search.periode ?? ""}
          options={PERIODS}
          onChange={(periode) => setListSearch({ periode })}
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
          unit="cohortes"
          sizes={PAGE_SIZES}
          value={pageSize}
          onChange={(size) => setListSearch({ par_page: String(size) })}
        />
        <span className="spacer" />
        {cohortes.isFetching && <WaSpinner />}
        <span className="muted">
          {plural(cohortes.data?.total ?? 0, "cohorte")} SOURCE
        </span>
      </div>
      {filtersOpen && fields.data && (
        <div className="fbwrap">
          <FilterBuilder
            fields={fields.data}
            value={filter}
            onApply={(next) => setListSearch({ filtre: serializeFilter(next) })}
          />
        </div>
      )}
      {cohortes.error && <p className="error">{cohortes.error.message}</p>}
      <div className="scroll grow">
        {items.length > 0 ? (
          <table className="tbl">
            <thead>
              <tr>
                {header("id", "#", "num")}
                {header("identifiant_action", "identifiant_action")}
                {header("type_action", "Type")}
                {header("statut", "Statut")}
                {header("identifiant_execution", "identifiant_execution")}
                {header("cree_le", "Créée le")}
                {header("total_groupes", "Groupes par statut")}
                {header("avalider", "Décidés", "num")}
                <th>Métadonnées</th>
                <th>Logs</th>
              </tr>
            </thead>
            <tbody>
              {items.map((cohorte, index) => (
                <CohorteRow
                  key={cohorte.id}
                  cohorte={cohorte}
                  focused={index === focus}
                  expanded={expanded.has(cohorte.id)}
                  href={buildHref(basepath, `/cohortes/${cohorte.id}`)}
                  onFocus={() => setFocus(() => index)}
                  onToggleMetadata={() =>
                    setExpanded((current) => {
                      const next = new Set(current)
                      if (!next.delete(cohorte.id)) {
                        next.add(cohorte.id)
                      }
                      return next
                    })
                  }
                  onOpenLogs={() => setSearch({ logs: String(cohorte.id) })}
                />
              ))}
            </tbody>
          </table>
        ) : (
          !cohortes.isPending && (
            <div className="emptystate">
              <b>Aucune cohorte ne correspond à ces filtres</b>
              Élargissez la période ou retirez une condition.
            </div>
          )
        )}
      </div>
      <div className="tfoot">
        <span>↑/↓ parcourir · ⏎ ouvrir · cliquez un en-tête pour trier</span>
        <span className="spacer" />
        {cohortes.data && (
          <Pager
            unit="cohortes"
            page={page}
            pageSize={pageSize}
            total={cohortes.data.total}
            onPage={(next) => setSearch({ page: String(next) })}
          />
        )}
      </div>
      <LogsDrawer
        cohorteId={logsCohorteId}
        onClose={() => setSearch({ logs: undefined })}
      />
    </main>
  )
}

function CohorteRow({
  cohorte,
  focused,
  expanded,
  href,
  onFocus,
  onToggleMetadata,
  onOpenLogs,
}: {
  cohorte: Cohorte
  focused: boolean
  expanded: boolean
  href: string
  onFocus: () => void
  onToggleMetadata: () => void
  onOpenLogs: () => void
}) {
  const counts = cohorte.compteurs
  const total = totalOf(counts)
  const decided = total ? Math.round(((total - counts.AVALIDER) / total) * 100) : 0
  const metadata =
    cohorte.metadata &&
    typeof cohorte.metadata === "object" &&
    !Array.isArray(cohorte.metadata)
      ? Object.entries(cohorte.metadata as Record<string, unknown>)
      : []
  return (
    <>
      <tr className={`clickable${focused ? " focus" : ""}`} onClick={onFocus}>
        <td className="num mono">{cohorte.id}</td>
        <td>
          <Link to={href} className="lk mono">
            {cohorte.identifiant_action}
          </Link>
          <span className="sub">exécution du {cohorte.execution_datetime}</span>
        </td>
        <td>
          <span className="type-tag" title={`Valeur stockée : ${cohorte.type_action}`}>
            {TYPE_ACTIONS[cohorte.type_action] ?? cohorte.type_action_label}
          </span>
        </td>
        <td>
          <CohorteStatutPill statut={cohorte.statut} />
        </td>
        <td className="mono">{cohorte.identifiant_execution}</td>
        <td className="mono">{formatDateTime(cohorte.cree_le)}</td>
        <td>
          <StackBar counts={counts} />
          <StatutLegend counts={counts} />
        </td>
        <td className="num mono">{decided} %</td>
        <td>
          {metadata.length > 0 && (
            <WaButton
              size="small"
              appearance="plain"
              aria-expanded={expanded}
              onClick={(event) => {
                event.stopPropagation()
                onToggleMetadata()
              }}
            >
              {expanded ? "▾" : "▸"} {plural(metadata.length, "clé")}
            </WaButton>
          )}
        </td>
        <td>
          <LogsButton cohorteId={cohorte.id} logs={cohorte.logs} onOpen={onOpenLogs} />
        </td>
      </tr>
      {expanded && (
        <tr className="metarow">
          <td />
          <td colSpan={9}>
            <dl className="metagrid">
              {metadata.map(([key, value]) => (
                <div key={key} className="metagrid__item">
                  <dt>metadata.{key}</dt>
                  <dd>{typeof value === "string" ? value : JSON.stringify(value)}</dd>
                </div>
              ))}
            </dl>
          </td>
        </tr>
      )}
    </>
  )
}
