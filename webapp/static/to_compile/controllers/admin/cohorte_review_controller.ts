import { Controller } from "@hotwired/stimulus"
import {
  ColumnDef,
  Table,
  TableState,
  Updater,
  createTable,
  getCoreRowModel,
} from "@tanstack/table-core"
import {
  Virtualizer,
  elementScroll,
  observeElementOffset,
  observeElementRect,
} from "@tanstack/virtual-core"

interface PivotCell {
  current: string | null
  suggested: string | null
  statut?: string
}

interface PivotRow {
  groupe_id: number
  statut: string
  statut_display: string
  acteur_id: string
  acteur_nom: string
  has_parent: boolean
  detail_url: string
  cells: Record<string, PivotCell>
  error?: string
}

interface FieldMeta {
  key: string
  pending: number
}

interface UndoEntry {
  id: number
  statut: string
}

interface RowsResponse {
  rows: PivotRow[]
  meta: {
    total: number
    next_after: number | null
    fields: FieldMeta[]
  }
}

const ROW_HEIGHT_ESTIMATE = 52
const OVERSCAN = 10
const LOAD_MORE_THRESHOLD = 20
const UNDO_TOAST_MS = 12000

const STATUT_PENDING = "AVALIDER"
const STATUT_ACCEPTED = "ATRAITER"
const STATUT_REJECTED = "REJETEE"

const CELL_STATE_CLASS: Record<string, string> = {
  [STATUT_PENDING]: "pending",
  [STATUT_ACCEPTED]: "accepted",
  [STATUT_REJECTED]: "rejected",
}

// Focus-mode query builder: lookups on the suggested value, mirroring the
// server-side REVIEW_VALUE_LOOKUPS allowlist
const VALUE_LOOKUPS: Array<[string, string]> = [
  ["startswith", "commence par"],
  ["endswith", "se termine par"],
  ["contains", "contient"],
  ["not_contains", "ne contient pas"],
  ["exact", "est exactement"],
  ["empty", "est vide"],
  ["not_empty", "n'est pas vide"],
]
const VALUE_LOOKUPS_WITHOUT_VALUE = new Set(["empty", "not_empty"])

interface ValueCondition {
  lookup: string
  value: string
}

interface ValueGroup {
  combinator: "et" | "ou"
  conditions: ValueCondition[]
}

interface ValueFilter {
  combinator: "et" | "ou"
  groups: ValueGroup[]
}

function blankValueCondition(): ValueCondition {
  return { lookup: "startswith", value: "" }
}

function blankValueGroup(): ValueGroup {
  return { combinator: "et", conditions: [blankValueCondition()] }
}

function esc(value: string | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return ""
  }
  const div = document.createElement("div")
  div.textContent = value
  // innerHTML escapes & < > but not quotes: needed because escaped values
  // are also interpolated into HTML attributes
  return div.innerHTML.replace(/"/g, "&quot;").replace(/'/g, "&#39;")
}

// esc() neutralises HTML but not a `javascript:` URI in an href. detail_url
// is server-built today, but validate the protocol defensively.
function safeHref(url: string | null | undefined): string {
  if (!url) {
    return "#"
  }
  try {
    const parsed = new URL(url, window.location.origin)
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return "#"
    }
    return esc(url)
  } catch {
    return "#"
  }
}

export default class extends Controller<HTMLElement> {
  static targets = [
    "scroller",
    "head",
    "body",
    "status",
    "fieldToggles",
    "pagerInfo",
    "loadMore",
    "bulkBar",
    "bulkCount",
    "bulkField",
    "search",
    "statutFilter",
    "focusLayout",
    "focusRail",
    "focusHeader",
    "focusCards",
    "selectFiltered",
    "announcer",
    "undoToast",
    "undoToastLabel",
    "drawer",
    "drawerBody",
    "drawerAdminLink",
  ]
  static values = {
    rowsUrl: String,
    bulkUrl: String,
    groupeUrlTemplate: String,
    adminUrlTemplate: String,
    csrf: String,
  }

  declare readonly scrollerTarget: HTMLDivElement
  declare readonly headTarget: HTMLTableSectionElement
  declare readonly bodyTarget: HTMLTableSectionElement
  declare readonly statusTarget: HTMLElement
  declare readonly fieldTogglesTarget: HTMLElement
  declare readonly pagerInfoTarget: HTMLElement
  declare readonly loadMoreTarget: HTMLElement
  declare readonly bulkBarTarget: HTMLElement
  declare readonly bulkCountTarget: HTMLElement
  declare readonly bulkFieldTarget: HTMLElement & { value: string }
  declare readonly searchTarget: HTMLElement & { value: string }
  declare readonly statutFilterTarget: HTMLElement & { value: string }
  declare readonly focusLayoutTarget: HTMLElement
  declare readonly focusRailTarget: HTMLElement
  declare readonly focusHeaderTarget: HTMLElement
  declare readonly focusCardsTarget: HTMLElement
  declare readonly selectFilteredTarget: HTMLElement
  declare readonly hasSelectFilteredTarget: boolean
  declare readonly announcerTarget: HTMLElement
  declare readonly undoToastTarget: HTMLElement
  declare readonly undoToastLabelTarget: HTMLElement
  declare readonly drawerTarget: HTMLElement & { show(): void; hide(): void }
  declare readonly drawerBodyTarget: HTMLElement
  declare readonly drawerAdminLinkTarget: HTMLElement & { href: string }
  declare readonly rowsUrlValue: string
  declare readonly bulkUrlValue: string
  declare readonly groupeUrlTemplateValue: string
  declare readonly adminUrlTemplateValue: string
  declare readonly csrfValue: string

  private rows: PivotRow[] = []
  private fields: FieldMeta[] = []
  private total = 0
  private nextAfter: number | null = 0
  private loading = false
  private q = ""
  private statutFilter = "AVALIDER"
  private searchDebounce: number | undefined
  private focusField: string | null = null
  private selectionScope: "ids" | "filter" = "ids"
  private activeCardIndex = 0
  // focus to restore after the next focus-header re-render (innerHTML
  // replacement destroys the control that triggered the action)
  private pendingHeaderFocus: string | null = null
  // applied filter (sent to the server) vs draft being edited in the builder
  private valueFilter: ValueFilter | null = null
  private builderGroups: ValueGroup[] = [blankValueGroup()]
  private builderCombinator: "et" | "ou" = "ou"
  // undo token of the last bulk action, surfaced via the « Annuler » toast
  private lastUndoToken: UndoEntry[] | null = null
  private undoToastTimer: number | undefined
  private table!: Table<PivotRow>
  private tableState!: TableState
  private virtualizer!: Virtualizer<HTMLDivElement, HTMLTableRowElement>
  private cleanupVirtualizer: () => void = () => {}

  connect() {
    this.initTable()
    this.initVirtualizer()
    // Cell action buttons and checkboxes are re-rendered on every scroll
    // (grid) or refresh (focus cards): delegated listeners survive instead
    // of re-binding, and avoid racing the custom-element upgrade.
    this.element.addEventListener("click", this.onCellAction)
    this.element.addEventListener("sl-change", this.onCheckboxChange)
    document.addEventListener("keydown", this.onKeydown)
    window.addEventListener("popstate", this.onPopstate)
    this.restoreStateFromUrl()
    this.applyFocusMode()
    this.fetchRows()
  }

  disconnect() {
    this.cleanupVirtualizer()
    this.element.removeEventListener("click", this.onCellAction)
    this.element.removeEventListener("sl-change", this.onCheckboxChange)
    document.removeEventListener("keydown", this.onKeydown)
    window.removeEventListener("popstate", this.onPopstate)
    window.clearTimeout(this.searchDebounce)
    window.clearTimeout(this.undoToastTimer)
  }

  // --- focus mode (review one field across all acteurs, ?focus=<champ>) ---

  private onKeydown = (event: KeyboardEvent) => {
    if (event.key === "Escape") {
      // when the drawer is open, Escape closes it (Shoelace handles that);
      // don't also exit focus mode in the same keystroke
      if (this.drawerGroupeId !== null) {
        return
      }
      if (this.focusField) {
        this.exitFocus()
        return
      }
    }
    // single-key shortcuts must never fire while typing in a field
    const target = event.target as HTMLElement
    if (
      event.metaKey ||
      event.ctrlKey ||
      event.altKey ||
      target.closest("input, select, textarea, sl-input, sl-select, [contenteditable]")
    ) {
      return
    }
    if (!this.focusField) {
      return
    }
    const handled = this.handleFocusModeKey(event.key)
    if (handled) {
      event.preventDefault()
    }
  }

  /** Focus-mode review loop: ↑/↓ (or k/j) move, A accept, R reject,
   * U undo, ⏎ opens the suggestion groupe of the active card. */
  private handleFocusModeKey(key: string): boolean {
    switch (key) {
      case "ArrowDown":
      case "j":
        this.moveActiveCard(1)
        return true
      case "ArrowUp":
      case "k":
        this.moveActiveCard(-1)
        return true
      case "a":
      case "A":
        this.decideActiveCard("accept")
        return true
      case "r":
      case "R":
        this.decideActiveCard("reject")
        return true
      case "u":
      case "U":
        this.decideActiveCard("reset", { advance: false })
        return true
      case "Enter": {
        const row = this.rows[this.activeCardIndex]
        if (row) {
          this.openGroupeDrawer(row.groupe_id)
        }
        return true
      }
      default:
        return false
    }
  }

  private moveActiveCard(delta: number) {
    if (!this.rows.length) {
      return
    }
    this.activeCardIndex = Math.max(
      0,
      Math.min(this.activeCardIndex + delta, this.rows.length - 1),
    )
    // refill the queue before the cursor reaches the end
    if (this.rows.length - this.activeCardIndex < LOAD_MORE_THRESHOLD) {
      this.fetchRows()
    }
    this.renderFocusCards()
    this.scrollActiveCardIntoView()
  }

  private decideActiveCard(
    action: string,
    { advance = true }: { advance?: boolean } = {},
  ) {
    const field = this.focusField
    const row = this.rows[this.activeCardIndex]
    if (!field || !row || !row.cells[field]) {
      return
    }
    this.postBulk([row.groupe_id], field, action)
    if (advance) {
      this.moveActiveCard(1)
    }
  }

  private scrollActiveCardIntoView() {
    this.focusCardsTarget
      .querySelector(".focus-card.active")
      ?.scrollIntoView({ block: "nearest" })
  }

  private onPopstate = () => {
    const params = new URLSearchParams(window.location.search)
    const field = params.get("focus")
    const q = params.get("q") ?? ""
    const statut = params.get("statut") ?? "AVALIDER"
    if (field === this.focusField && q === this.q && statut === this.statutFilter) {
      return
    }
    this.focusField = field
    this.q = q
    this.statutFilter = statut
    this.resetValueFilter()
    this.applyFocusMode()
    this.resetAndFetch()
  }

  focusOn(event: Event) {
    const field = (event.currentTarget as HTMLElement).dataset.field
    if (!field || field === this.focusField) {
      return
    }
    this.focusField = field
    this.resetValueFilter()
    this.syncFocusToUrl()
    this.applyFocusMode()
    this.resetAndFetch()
    // the trigger button lives in the (now hidden) grid header: move focus
    // into the focus layout so keyboard review can start immediately
    this.focusCardsTarget.focus()
    this.announce(`Mode focus sur le champ ${field}`)
  }

  exitFocus() {
    this.focusField = null
    this.resetValueFilter()
    this.syncFocusToUrl()
    this.applyFocusMode()
    this.resetAndFetch()
    this.searchTarget.focus?.()
    this.announce("Retour à la grille")
  }

  // --- focus-mode query builder on the suggested value ---

  vbAddCondition(event: Event) {
    this.readBuilderFromDom()
    const groupIndex = Number((event.currentTarget as HTMLElement).dataset.group)
    this.builderGroups[groupIndex]?.conditions.push(blankValueCondition())
    this.pendingHeaderFocus = `[data-action*="vbAddCondition"][data-group="${groupIndex}"]`
    this.renderFocusHeader()
  }

  vbRemoveCondition(event: Event) {
    this.readBuilderFromDom()
    const button = event.currentTarget as HTMLElement
    const group = this.builderGroups[Number(button.dataset.group)]
    group?.conditions.splice(Number(button.dataset.index), 1)
    if (group && !group.conditions.length) {
      group.conditions = [blankValueCondition()]
    }
    this.renderFocusHeader()
  }

  vbAddGroup() {
    this.readBuilderFromDom()
    this.builderGroups.push(blankValueGroup())
    this.renderFocusHeader()
  }

  vbRemoveGroup(event: Event) {
    this.readBuilderFromDom()
    const groupIndex = Number((event.currentTarget as HTMLElement).dataset.group)
    this.builderGroups.splice(groupIndex, 1)
    if (!this.builderGroups.length) {
      this.builderGroups = [blankValueGroup()]
    }
    this.renderFocusHeader()
  }

  vbLookupChanged() {
    // value inputs are shown/hidden depending on the lookup
    this.readBuilderFromDom()
    this.renderFocusHeader()
  }

  vbApply() {
    this.readBuilderFromDom()
    this.pendingHeaderFocus = `[data-action*="vbApply"]`
    const groups = this.builderGroups
      .map((group) => ({
        combinator: group.combinator,
        conditions: group.conditions.filter(
          (condition) =>
            VALUE_LOOKUPS_WITHOUT_VALUE.has(condition.lookup) ||
            condition.value.trim() !== "",
        ),
      }))
      .filter((group) => group.conditions.length)
    this.valueFilter = groups.length
      ? { combinator: this.builderCombinator, groups }
      : null
    this.resetAndFetch()
  }

  vbClear() {
    this.resetValueFilter()
    this.resetAndFetch()
  }

  private resetValueFilter() {
    this.valueFilter = null
    this.builderGroups = [blankValueGroup()]
    this.builderCombinator = "ou"
  }

  private readBuilderFromDom() {
    const groupElements = [...this.focusHeaderTarget.querySelectorAll(".vb-group")]
    if (groupElements.length) {
      this.builderGroups = groupElements.map((groupElement) => ({
        combinator:
          (
            groupElement.querySelector(
              ".vb-group-combinator",
            ) as HTMLSelectElement | null
          )?.value === "ou"
            ? "ou"
            : "et",
        conditions: [...groupElement.querySelectorAll(".vb-row")].map((row) => ({
          lookup: (row.querySelector(".vb-lookup") as HTMLSelectElement).value,
          value:
            (row.querySelector(".vb-value") as HTMLInputElement | null)?.value ?? "",
        })),
      }))
    }
    const topCombinator = this.focusHeaderTarget.querySelector(
      ".vb-top-combinator",
    ) as HTMLSelectElement | null
    if (topCombinator) {
      this.builderCombinator = topCombinator.value === "et" ? "et" : "ou"
    }
  }

  acceptAllLoaded() {
    if (!this.focusField) {
      return
    }
    const field = this.focusField
    const pendingIds = this.rows
      .filter((row) => row.cells[field]?.statut === STATUT_PENDING)
      .map((row) => row.groupe_id)
    this.postBulk(pendingIds, field, "accept")
  }

  private syncFocusToUrl() {
    window.history.pushState({}, "", this.buildStateUrl())
  }

  private syncFiltersToUrl() {
    // filters replace (no history spam); mode changes push (back works)
    window.history.replaceState({}, "", this.buildStateUrl())
  }

  private buildStateUrl(): URL {
    const url = new URL(window.location.href)
    const setOrDelete = (key: string, value: string, defaultValue: string) => {
      if (value && value !== defaultValue) {
        url.searchParams.set(key, value)
      } else {
        url.searchParams.delete(key)
      }
    }
    setOrDelete("focus", this.focusField ?? "", "")
    setOrDelete("q", this.q, "")
    setOrDelete("statut", this.statutFilter, "AVALIDER")
    return url
  }

  private applyFocusMode() {
    this.element.classList.toggle("focus-mode", this.focusField !== null)
    this.focusLayoutTarget.toggleAttribute("hidden", this.focusField === null)
  }

  // --- data loading ---

  async fetchRows() {
    if (this.loading || this.nextAfter === null) {
      return
    }
    this.loading = true
    this.renderStatus()
    try {
      const url = new URL(this.rowsUrlValue, window.location.origin)
      url.searchParams.set("after", String(this.nextAfter))
      url.searchParams.set("statut", this.statutFilter)
      if (this.q) {
        url.searchParams.set("q", this.q)
      }
      if (this.focusField) {
        url.searchParams.set("champ", this.focusField)
        if (this.valueFilter) {
          url.searchParams.set("valeur_filtre", JSON.stringify(this.valueFilter))
        }
      }
      const response = await fetch(url, {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const payload: RowsResponse = await response.json()
      this.rows = [...this.rows, ...payload.rows]
      this.total = payload.meta.total
      this.nextAfter = payload.meta.next_after
      if (!this.fields.length) {
        this.fields = payload.meta.fields
        this.renderFieldToggles()
        this.renderBulkFieldOptions()
        this.renderHead()
      }
      this.table.setOptions((prev) => ({
        ...prev,
        data: this.rows,
        columns: this.buildColumns(),
      }))
      this.virtualizer.setOptions({
        ...this.virtualizer.options,
        count: this.rows.length,
      })
      this.renderAll()
    } catch (error) {
      this.statusTarget.textContent = `Erreur de chargement (${error}) — rechargez la page`
    } finally {
      this.loading = false
      this.renderStatus()
    }
  }

  loadMore() {
    this.fetchRows()
  }

  // --- filters (server-side: changing them reloads from the first batch) ---

  onSearchInput() {
    window.clearTimeout(this.searchDebounce)
    this.searchDebounce = window.setTimeout(() => {
      this.q = this.searchTarget.value.trim()
      this.syncFiltersToUrl()
      this.resetAndFetch()
    }, 300)
  }

  onStatutChange() {
    this.statutFilter = this.statutFilterTarget.value || "AVALIDER"
    this.syncFiltersToUrl()
    this.resetAndFetch()
  }

  private resetAndFetch() {
    this.rows = []
    this.total = 0
    this.nextAfter = 0
    this.selectionScope = "ids"
    this.activeCardIndex = 0
    this.table.resetRowSelection(true)
    this.table.setOptions((prev) => ({ ...prev, data: this.rows }))
    this.virtualizer.setOptions({ ...this.virtualizer.options, count: 0 })
    this.scrollerTarget.scrollTop = 0
    this.renderAll()
    this.fetchRows()
  }

  // --- mutations (per-cell and bulk accept/reject) ---

  bulkAccept() {
    this.bulkAction("accept")
  }

  bulkReject() {
    this.bulkAction("reject")
  }

  selectAllFiltered() {
    this.selectionScope = "filter"
    this.renderStatus()
  }

  clearSelection() {
    this.selectionScope = "ids"
    this.table.toggleAllRowsSelected(false)
  }

  private bulkAction(action: string) {
    const champ = this.bulkFieldTarget.value
    if (this.selectionScope === "filter") {
      // Filter scope acts beyond the loaded rows. Checked rows in this scope
      // mean « tout sauf ceux-là », so they become exclusions.
      const excludeIds = this.selectedGroupeIds()
      const netCount = this.total - excludeIds.length
      const target = champ ? `le champ « ${champ} »` : "tous les champs"
      const verb = action === "accept" ? "Accepter" : "Rejeter"
      const except = excludeIds.length
        ? ` (sauf ${excludeIds.length} exclu${excludeIds.length > 1 ? "s" : ""})`
        : ""
      const confirmed = window.confirm(
        `${verb} ${target} pour les ${netCount} acteurs filtrés${except} ?\n` +
          `Cette action s'applique à tous les acteurs correspondant aux ` +
          `filtres, au-delà des lignes chargées.`,
      )
      if (!confirmed) {
        return
      }
      this.sendBulk(
        {
          filter: {
            statut: this.statutFilter,
            champ: this.focusField,
            q: this.q || null,
            valeur_filtre: this.focusField ? this.valueFilter : null,
            exclude_ids: excludeIds.length ? excludeIds : undefined,
          },
          champ: champ || null,
          action,
        },
        { reload: true },
      )
    } else {
      this.postBulk(this.selectedGroupeIds(), champ, action)
    }
  }

  // arrow-function properties so add/removeEventListener share one identity
  private onCellAction = (event: Event) => {
    const button = (event.target as HTMLElement).closest<HTMLElement>(
      "[data-cell-action]",
    )
    if (!button) {
      this.maybeOpenFocusCard(event)
      return
    }
    event.preventDefault()
    this.postBulk(
      [Number(button.dataset.groupeId)],
      button.dataset.field ?? "",
      button.dataset.cellAction as string,
    )
  }

  private onCheckboxChange = (event: Event) => {
    const target = event.target as HTMLElement & { checked: boolean }
    if (target.hasAttribute("data-select-all")) {
      this.table.toggleAllRowsSelected(target.checked)
      return
    }
    const rowId = target.dataset.rowSelect
    if (rowId) {
      this.table.getRow(rowId).toggleSelected(target.checked)
    }
  }

  private restoreStateFromUrl() {
    const params = new URLSearchParams(window.location.search)
    this.focusField = params.get("focus")
    this.q = params.get("q") ?? ""
    this.statutFilter = params.get("statut") ?? "AVALIDER"
    // sl components upgrade asynchronously: set their values once defined
    customElements.whenDefined("sl-input").then(() => {
      this.searchTarget.value = this.q
    })
    customElements.whenDefined("sl-select").then(() => {
      this.statutFilterTarget.value = this.statutFilter
    })
  }

  private maybeOpenFocusCard(event: Event) {
    // In focus mode the whole card opens the acteur's suggestion groupe in a
    // drawer, except clicks on its interactive elements (actions, links)
    const target = event.target as HTMLElement
    const card = target.closest<HTMLElement>(".focus-card[data-groupe-id]")
    if (!card || target.closest("a, button, sl-button, input, select")) {
      return
    }
    this.openGroupeDrawer(Number(card.dataset.groupeId))
  }

  // --- suggestion-groupe drawer (act on all of an acteur's fields) ---

  openGroupeFromCard(event: Event) {
    event.preventDefault()
    const id = (event.currentTarget as HTMLElement).dataset.groupeId
    if (id) {
      this.openGroupeDrawer(Number(id))
    }
  }

  private drawerGroupeId: number | null = null

  private async openGroupeDrawer(groupeId: number) {
    this.drawerGroupeId = groupeId
    this.drawerBodyTarget.innerHTML = `<p class="drawer-loading">Chargement…</p>`
    this.drawerAdminLinkTarget.href = this.adminUrlTemplateValue.replace(
      "/0/",
      `/${groupeId}/`,
    )
    this.drawerTarget.show()
    await this.refreshDrawer()
  }

  private async refreshDrawer() {
    if (this.drawerGroupeId === null) {
      return
    }
    const url = this.groupeUrlTemplateValue.replace(
      /\/0\/$/,
      `/${this.drawerGroupeId}/`,
    )
    try {
      const response = await fetch(url, {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const payload = await response.json()
      this.renderDrawer(payload.row as PivotRow)
    } catch (error) {
      this.drawerBodyTarget.innerHTML = `<p class="drawer-error">Erreur de chargement (${esc(String(error))})</p>`
    }
  }

  private renderDrawer(row: PivotRow) {
    this.drawerTarget.setAttribute("label", row.acteur_nom || row.acteur_id || "Acteur")
    const fieldRows = Object.entries(row.cells)
      .map(([field, cell]) => {
        const statut = cell.statut ?? STATUT_PENDING
        const stateClass = CELL_STATE_CLASS[statut] ?? "pending"
        const current =
          cell.current !== null && cell.current !== cell.suggested
            ? `<span class="old">${esc(cell.current)}</span>`
            : ""
        return `
          <tr class="drawer-field sug ${stateClass}">
            <th scope="row">${esc(field)}</th>
            <td class="drawer-diff">
              ${current}
              <span class="new">${esc(cell.suggested ?? "") || "—"}</span>
            </td>
            <td class="drawer-actions">
              ${this.renderCellActions(row.groupe_id, field, statut)}
            </td>
          </tr>`
      })
      .join("")
    const hasPending = Object.values(row.cells).some(
      (cell) => (cell.statut ?? STATUT_PENDING) === STATUT_PENDING,
    )
    this.drawerBodyTarget.innerHTML = `
      <p class="drawer-sub">${esc(row.acteur_id)} · ${esc(row.statut_display)}</p>
      <table class="drawer-table">
        <tbody>${fieldRows}</tbody>
      </table>
      <div class="drawer-bulk">
        <sl-button size="small" variant="success"
          data-action="click->cohorte-review#drawerAcceptAll"
          ${hasPending ? "" : "disabled"}>✓ Tout accepter</sl-button>
        <sl-button size="small" variant="danger" outline
          data-action="click->cohorte-review#drawerRejectAll"
          ${hasPending ? "" : "disabled"}>✕ Tout rejeter</sl-button>
      </div>`
  }

  drawerAcceptAll() {
    if (this.drawerGroupeId !== null) {
      this.postBulk([this.drawerGroupeId], "", "accept")
    }
  }

  drawerRejectAll() {
    if (this.drawerGroupeId !== null) {
      this.postBulk([this.drawerGroupeId], "", "reject")
    }
  }

  onDrawerClosed(event: Event) {
    // sl-after-hide bubbles; only react to the drawer's own event
    if (event.target === this.drawerTarget) {
      this.drawerGroupeId = null
    }
  }

  private selectedGroupeIds(): number[] {
    return Object.entries(this.tableState.rowSelection ?? {})
      .filter(([, isSelected]) => isSelected)
      .map(([groupeId]) => Number(groupeId))
  }

  private postBulk(groupeIds: number[], champ: string, action: string) {
    if (!groupeIds.length) {
      return
    }
    // Optimistic: the cells flip immediately, the server response (or a
    // rollback on error) reconciles afterwards. Decisions never wait.
    const snapshot = this.applyOptimistic(groupeIds, champ || null, action)
    this.sendBulk(
      { groupe_ids: groupeIds, champ: champ || null, action },
      { reload: false, snapshot },
    )
  }

  private applyOptimistic(
    groupeIds: number[],
    champ: string | null,
    action: string,
  ): PivotRow[] {
    const statut =
      action === "accept"
        ? STATUT_ACCEPTED
        : action === "reject"
          ? STATUT_REJECTED
          : STATUT_PENDING
    const ids = new Set(groupeIds)
    const snapshot: PivotRow[] = []
    this.rows = this.rows.map((row) => {
      if (!ids.has(row.groupe_id)) {
        return row
      }
      snapshot.push(row)
      const cells: Record<string, PivotCell> = {}
      for (const [field, cell] of Object.entries(row.cells)) {
        cells[field] = !champ || field === champ ? { ...cell, statut } : cell
      }
      return { ...row, cells }
    })
    this.table.setOptions((prev) => ({ ...prev, data: this.rows }))
    this.renderAll()
    return snapshot
  }

  private async sendBulk(
    body: object,
    { reload, snapshot = [] }: { reload: boolean; snapshot?: PivotRow[] },
  ) {
    try {
      const response = await fetch(this.bulkUrlValue, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.csrfValue,
          Accept: "application/json",
        },
        credentials: "same-origin",
        body: JSON.stringify(body),
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const payload = await response.json()
      this.fields = this.mergeFieldsMeta(payload.meta.fields as FieldMeta[])
      if (payload.rows) {
        this.mergeRows(payload.rows as PivotRow[])
      }
      const isUndo = (body as { action?: string }).action === "undo"
      const message = isUndo
        ? "Action annulée"
        : this.describeBulkResult(payload.applied, body)
      this.announce(message)
      if (!isUndo) {
        this.maybeShowUndoToast(body, payload, message)
      }
      if (reload) {
        // Filter-scope mutations touch rows beyond the loaded window:
        // reload from the first batch instead of merging.
        this.resetAndFetch()
        return
      }
      this.renderAll()
    } catch (error) {
      if (snapshot.length) {
        this.mergeRows(snapshot)
        this.renderAll()
      }
      this.statusTarget.textContent = `Erreur lors de l'action (${error})`
      this.announce("L'action a échoué, la suggestion n'a pas été modifiée")
    }
  }

  private describeBulkResult(applied: number, body: object): string {
    const action = (body as { action?: string }).action
    const verb =
      action === "accept"
        ? "acceptée"
        : action === "reject"
          ? "rejetée"
          : "remise à valider"
    return `${applied} suggestion${applied > 1 ? "s" : ""} ${verb}${
      applied > 1 ? "s" : ""
    }`
  }

  private announce(message: string) {
    this.announcerTarget.textContent = message
  }

  // --- undo toast ---

  private maybeShowUndoToast(
    body: object,
    payload: { applied: number; undo?: UndoEntry[] },
    message: string,
  ) {
    const action = (body as { action?: string }).action
    const undo = payload.undo
    // the per-cell ↺ already covers single decisions; only offer undo where
    // there is no other easy way back (bulk, or any reject)
    const isBulk = (body as { filter?: unknown }).filter !== undefined
    const worthUndo = action === "reject" || isBulk || (payload.applied ?? 0) > 1
    if (!action || !undo || !undo.length || !worthUndo) {
      return
    }
    this.lastUndoToken = undo
    this.undoToastLabelTarget.textContent = message
    this.undoToastTarget.hidden = false
    window.clearTimeout(this.undoToastTimer)
    this.undoToastTimer = window.setTimeout(
      () => this.dismissUndoToast(),
      UNDO_TOAST_MS,
    )
  }

  dismissUndoToast() {
    window.clearTimeout(this.undoToastTimer)
    this.undoToastTarget.hidden = true
    this.lastUndoToken = null
  }

  undoLastBulk() {
    if (!this.lastUndoToken) {
      return
    }
    const token = this.lastUndoToken
    this.dismissUndoToast()
    this.sendBulk({ action: "undo", undo: token }, { reload: false })
  }

  private mergeRows(updatedRows: PivotRow[]) {
    const byId = new Map(updatedRows.map((row) => [row.groupe_id, row]))
    this.rows = this.rows.map((row) => byId.get(row.groupe_id) ?? row)
    this.table.setOptions((prev) => ({ ...prev, data: this.rows }))
    // keep the open drawer in sync when its groupe was just mutated
    if (this.drawerGroupeId !== null && byId.has(this.drawerGroupeId)) {
      this.renderDrawer(byId.get(this.drawerGroupeId) as PivotRow)
    }
  }

  private mergeFieldsMeta(updated: FieldMeta[]): FieldMeta[] {
    // Keep the columns discovered at first load (a fully-decided field
    // disappears from the server meta but its column must survive), only
    // refresh the pending counts.
    const pendingByKey = new Map(updated.map((field) => [field.key, field.pending]))
    return this.fields.map((field) => ({
      ...field,
      pending: pendingByKey.get(field.key) ?? 0,
    }))
  }

  // --- tanstack table (headless state: column visibility, row selection) ---

  private initTable() {
    // We do our own cursor pagination, so the table must not paginate the
    // data itself. A complete initial state (incl. pagination) is required:
    // row-selection internals read state.pagination.pageIndex.
    this.tableState = {
      columnVisibility: {},
      rowSelection: {},
      pagination: { pageIndex: 0, pageSize: Number.MAX_SAFE_INTEGER },
    } as TableState

    this.table = createTable<PivotRow>({
      data: [],
      columns: [],
      state: this.tableState,
      manualPagination: true,
      onStateChange: (updater: Updater<TableState>) => {
        this.tableState =
          updater instanceof Function ? updater(this.tableState) : updater
        this.table.setOptions((prev) => ({ ...prev, state: this.tableState }))
        this.renderAll()
      },
      getCoreRowModel: getCoreRowModel(),
      getRowId: (row) => String(row.groupe_id),
      renderFallbackValue: null,
    })
  }

  private buildColumns(): ColumnDef<PivotRow>[] {
    return this.fields.map((field) => ({
      id: field.key,
      accessorFn: (row) => row.cells[field.key] ?? null,
    }))
  }

  private visibleFields(): FieldMeta[] {
    const visibility = this.tableState.columnVisibility ?? {}
    return this.fields.filter((field) => visibility[field.key] !== false)
  }

  // --- virtualization ---

  private initVirtualizer() {
    this.virtualizer = new Virtualizer<HTMLDivElement, HTMLTableRowElement>({
      count: 0,
      getScrollElement: () => this.scrollerTarget,
      estimateSize: () => ROW_HEIGHT_ESTIMATE,
      overscan: OVERSCAN,
      scrollToFn: elementScroll,
      observeElementRect,
      observeElementOffset,
      onChange: () => this.renderBody(),
    })
    this.cleanupVirtualizer = this.virtualizer._didMount()
  }

  // --- rendering ---

  private renderAll() {
    if (this.focusField) {
      this.renderFocusRail()
      this.renderFocusHeader()
      this.renderFocusCards()
    } else {
      this.renderHead()
      this.renderBody()
    }
    this.renderStatus()
  }

  private renderFocusRail() {
    const items = this.fields
      .map((field) => {
        const badge = field.pending
          ? `<sl-badge variant="warning" pill>${field.pending}</sl-badge>`
          : `<sl-badge variant="success" pill>✓</sl-badge>`
        return `
          <button type="button"
            class="field-item ${field.key === this.focusField ? "active" : ""}"
            data-action="click->cohorte-review#focusOn"
            data-field="${esc(field.key)}">
            ${esc(field.key)} ${badge}
          </button>`
      })
      .join("")
    this.focusRailTarget.innerHTML = `<h2>Champs</h2>${items}`
  }

  private renderFocusHeader() {
    const field = this.focusField as string
    const pending = this.fields.find((meta) => meta.key === field)?.pending ?? 0
    const loadedPending = this.rows.filter(
      (row) => row.cells[field]?.statut === STATUT_PENDING,
    ).length
    this.focusHeaderTarget.innerHTML = `
      <div class="focus-header">
        <h1>Mode focus — champ <code>${esc(field)}</code>
          <span class="remaining">${pending} à valider</span>
        </h1>
        <div class="focus-actions">
          <sl-button size="small" variant="success"
            data-action="click->cohorte-review#acceptAllLoaded"
            ${loadedPending ? "" : "disabled"}>
            ✓ Accepter les ${loadedPending} chargées
          </sl-button>
          <sl-button size="small" variant="default"
            data-action="click->cohorte-review#exitFocus">
            ← Quitter le mode focus (Échap)
          </sl-button>
        </div>
      </div>
      ${this.renderValueBuilder(field)}`
    if (this.pendingHeaderFocus) {
      const element = this.focusHeaderTarget.querySelector(
        this.pendingHeaderFocus,
      ) as HTMLElement | null
      // a fresh sl-button may not have upgraded its shadow root yet:
      // focus() can throw inside the component (best-effort restoration)
      try {
        element?.focus()
      } catch {
        // ignore
      }
      this.pendingHeaderFocus = null
    }
  }

  private renderValueBuilder(field: string): string {
    const groupsHtml = this.builderGroups
      .map((group, groupIndex) => this.renderValueGroup(group, groupIndex))
      .join(
        `<div class="vb-between-groups" aria-hidden="true">
          ${this.builderCombinator === "et" ? "ET" : "OU"}
        </div>`,
      )

    const topCombinator =
      this.builderGroups.length > 1
        ? `<label class="vb-top">groupes combinés par
            <select class="vb-top-combinator"
              data-action="change->cohorte-review#vbLookupChanged"
              aria-label="Combinaison entre les groupes">
              <option value="ou" ${this.builderCombinator === "ou" ? "selected" : ""}>
                OU (au moins un groupe)
              </option>
              <option value="et" ${this.builderCombinator === "et" ? "selected" : ""}>
                ET (tous les groupes)
              </option>
            </select>
          </label>`
        : ""

    const filterActions = this.valueFilter
      ? `<span class="vb-active">filtre actif — ${this.total} correspondant${
          this.total > 1 ? "s" : ""
        }</span>
        <sl-button size="small" variant="success"
          data-action="click->cohorte-review#focusBulkAccept"
          ${this.total ? "" : "disabled"}>
          ✓ Accepter les ${this.total} filtrées
        </sl-button>
        <sl-button size="small" variant="danger" outline
          data-action="click->cohorte-review#focusBulkReject"
          ${this.total ? "" : "disabled"}>
          ✕ Rejeter les ${this.total} filtrées
        </sl-button>`
      : ""

    return `
      <div class="value-builder">
        <span class="vb-label">Filtrer la valeur suggérée de <code>${esc(field)}</code> :</span>
        ${groupsHtml}
        <div class="vb-footer">
          ${topCombinator}
          <button type="button" class="vb-add"
            data-action="click->cohorte-review#vbAddGroup">＋ groupe</button>
          <sl-button size="small" variant="primary"
            data-action="click->cohorte-review#vbApply">Appliquer</sl-button>
          <sl-button size="small" variant="text"
            data-action="click->cohorte-review#vbClear">Effacer</sl-button>
          ${filterActions}
        </div>
      </div>`
  }

  private renderValueGroup(group: ValueGroup, groupIndex: number): string {
    const conditionRows = group.conditions
      .map((condition, index) => {
        const options = VALUE_LOOKUPS.map(
          ([key, label]) =>
            `<option value="${key}" ${key === condition.lookup ? "selected" : ""}>
              ${label}
            </option>`,
        ).join("")
        const valueInput = VALUE_LOOKUPS_WITHOUT_VALUE.has(condition.lookup)
          ? ""
          : `<input type="text" class="vb-value" value="${esc(condition.value)}"
              placeholder="ex : 07"
              aria-label="Valeur de la condition ${index + 1} du groupe ${groupIndex + 1}">`
        const lineCombinator = index
          ? `<span class="vb-line-combinator">${
              group.combinator === "ou" ? "OU" : "ET"
            }</span>`
          : `<span class="vb-line-combinator" aria-hidden="true"></span>`
        return `
          <div class="vb-row">
            ${lineCombinator}
            <select class="vb-lookup"
              aria-label="Opérateur de la condition ${index + 1} du groupe ${groupIndex + 1}"
              data-action="change->cohorte-review#vbLookupChanged">${options}</select>
            ${valueInput}
            <button type="button" class="vb-remove" title="Supprimer la condition"
              data-action="click->cohorte-review#vbRemoveCondition"
              data-group="${groupIndex}" data-index="${index}">✕</button>
          </div>`
      })
      .join("")

    const groupCombinator =
      group.conditions.length > 1
        ? `<label>conditions combinées par
            <select class="vb-group-combinator"
              data-action="change->cohorte-review#vbLookupChanged"
              aria-label="Combinaison des conditions du groupe ${groupIndex + 1}">
              <option value="et" ${group.combinator === "et" ? "selected" : ""}>ET</option>
              <option value="ou" ${group.combinator === "ou" ? "selected" : ""}>OU</option>
            </select>
          </label>`
        : `<select class="vb-group-combinator" hidden>
            <option value="${group.combinator}" selected></option>
          </select>`

    const removeGroup =
      this.builderGroups.length > 1
        ? `<button type="button" class="vb-remove" title="Supprimer le groupe"
            data-action="click->cohorte-review#vbRemoveGroup"
            data-group="${groupIndex}">✕ groupe</button>`
        : ""

    return `
      <fieldset class="vb-group">
        <legend>Groupe ${groupIndex + 1}</legend>
        <div class="vb-group-head">
          ${groupCombinator}
          ${removeGroup}
        </div>
        ${conditionRows}
        <button type="button" class="vb-add"
          data-action="click->cohorte-review#vbAddCondition"
          data-group="${groupIndex}">＋ condition</button>
      </fieldset>`
  }

  focusBulkAccept() {
    this.focusBulkAction("accept")
  }

  focusBulkReject() {
    this.focusBulkAction("reject")
  }

  private focusBulkAction(action: string) {
    const field = this.focusField
    if (!field) {
      return
    }
    const verb = action === "accept" ? "Accepter" : "Rejeter"
    const confirmed = window.confirm(
      `${verb} « ${field} » pour les ${this.total} acteurs correspondant ` +
        `au filtre ?\nCette action s'applique au-delà des lignes chargées.`,
    )
    if (!confirmed) {
      return
    }
    this.sendBulk(
      {
        filter: {
          statut: this.statutFilter,
          champ: field,
          q: this.q || null,
          valeur_filtre: this.valueFilter,
        },
        champ: field,
        action,
      },
      { reload: true },
    )
  }

  private renderFocusCards() {
    const field = this.focusField as string
    this.activeCardIndex = Math.max(
      0,
      Math.min(this.activeCardIndex, this.rows.length - 1),
    )
    const cards = this.rows
      .map((row, index) =>
        this.renderFocusCard(row, field, index === this.activeCardIndex),
      )
      .join("")
    this.focusCardsTarget.innerHTML =
      cards || `<p class="focus-empty">Aucune suggestion pour ce champ.</p>`
  }

  private renderFocusCard(row: PivotRow, field: string, isActive: boolean): string {
    const cell = row.cells[field]
    if (!cell) {
      return ""
    }
    const statut = cell.statut ?? STATUT_PENDING
    const stateClass = CELL_STATE_CLASS[statut] ?? "pending"
    const current =
      cell.current !== null && cell.current !== cell.suggested
        ? `<span class="old">${esc(cell.current)}</span>`
        : ""
    return `
      <div class="focus-card ${stateClass} ${isActive ? "active" : ""}"
        data-groupe-id="${row.groupe_id}"
        title="Voir toutes les suggestions de cet acteur">
        <div class="who">
          <button type="button" class="acteur-nom"
            data-action="click->cohorte-review#openGroupeFromCard"
            data-groupe-id="${row.groupe_id}">${esc(row.acteur_nom) || "(sans nom)"}</button>
          <span class="acteur-id">${esc(row.acteur_id)}</span>
        </div>
        <div class="diff">
          ${current}
          <span class="new">${esc(cell.suggested ?? "") || "—"}</span>
        </div>
        ${this.renderCellActions(row.groupe_id, field, statut)}
      </div>`
  }

  private renderHead() {
    const fieldHeads = this.visibleFields()
      .map(
        (field) => `
          <th scope="col">
            ${esc(field.key)}
            <button type="button" class="focus-entry"
              data-action="click->cohorte-review#focusOn"
              data-field="${esc(field.key)}"
              aria-label="Réviser le champ ${esc(field.key)} en mode focus (${field.pending} suggestions à valider)">
              <sl-badge variant="warning" pill>${field.pending} <span aria-hidden="true">🎯</span></sl-badge>
            </button>
          </th>`,
      )
      .join("")
    this.headTarget.innerHTML = `
      <tr>
        <th scope="col" class="col-select">
          <sl-checkbox size="small" data-select-all
            aria-label="Sélectionner les lignes chargées"></sl-checkbox>
        </th>
        <th scope="col" class="col-acteur">Acteur</th>
        ${fieldHeads}
      </tr>`
  }

  private renderBody() {
    if (!this.rows.length) {
      this.bodyTarget.innerHTML = ""
      return
    }
    this.virtualizer._willUpdate()
    const virtualItems = this.virtualizer.getVirtualItems()
    if (!virtualItems.length) {
      return
    }
    const totalSize = this.virtualizer.getTotalSize()
    const paddingTop = virtualItems[0].start
    const paddingBottom = totalSize - virtualItems[virtualItems.length - 1].end
    const columnCount = this.visibleFields().length + 2

    const renderedRows = virtualItems
      .map((virtualItem) =>
        this.renderRow(this.rows[virtualItem.index], virtualItem.index),
      )
      .join("")

    // innerHTML replacement destroys the focused element: snapshot its
    // logical identity and restore focus after the re-render
    const focusSnapshot = this.snapshotBodyFocus()
    this.bodyTarget.innerHTML = `
      ${this.spacerRow(paddingTop, columnCount)}
      ${renderedRows}
      ${this.spacerRow(paddingBottom, columnCount)}`
    this.restoreBodyFocus(focusSnapshot)

    const lastIndex = virtualItems[virtualItems.length - 1].index
    if (lastIndex >= this.rows.length - LOAD_MORE_THRESHOLD) {
      this.fetchRows()
    }
  }

  private snapshotBodyFocus(): string | null {
    const active = document.activeElement as HTMLElement | null
    if (!active || !this.bodyTarget.contains(active)) {
      return null
    }
    // CSS.escape every interpolated value: field keys could in principle
    // contain selector-special characters
    if (active.dataset.rowSelect) {
      return `[data-row-select="${CSS.escape(active.dataset.rowSelect)}"]`
    }
    if (active.dataset.cellAction) {
      return (
        `[data-cell-action="${CSS.escape(active.dataset.cellAction)}"]` +
        `[data-groupe-id="${CSS.escape(active.dataset.groupeId ?? "")}"]` +
        `[data-field="${CSS.escape(active.dataset.field ?? "")}"]`
      )
    }
    const row = active.closest("[data-groupe-id]") as HTMLElement | null
    return row ? `[data-groupe-id="${CSS.escape(row.dataset.groupeId ?? "")}"] a` : null
  }

  private restoreBodyFocus(selector: string | null) {
    if (!selector) {
      return
    }
    const element = this.bodyTarget.querySelector(selector) as HTMLElement | null
    if (!element) {
      return
    }
    // A just-rendered sl-checkbox may not have upgraded its shadow root yet:
    // calling focus() synchronously can throw inside the component. Guard it.
    try {
      element.focus()
    } catch {
      // ignore: focus restoration is best-effort
    }
  }

  private spacerRow(height: number, columnCount: number): string {
    if (height <= 0) {
      return ""
    }
    return `<tr aria-hidden="true" class="spacer">
      <td colspan="${columnCount}" style="height:${height}px; padding:0; border:0"></td>
    </tr>`
  }

  private renderRow(row: PivotRow, virtualIndex: number): string {
    const isSelected = this.tableState.rowSelection?.[String(row.groupe_id)] === true
    const cells = this.visibleFields()
      .map((field) => this.renderCell(row, field.key))
      .join("")
    const parentBadge = row.has_parent
      ? `<sl-badge variant="primary" pill>parent</sl-badge>`
      : ""
    const errorNote = row.error
      ? `<span class="row-error">${esc(row.error)}</span>`
      : ""
    return `
      <tr class="${isSelected ? "selected" : ""}" data-groupe-id="${row.groupe_id}"
        aria-rowindex="${virtualIndex + 2}">
        <td class="col-select">
          <sl-checkbox size="small" data-row-select="${row.groupe_id}"
            ${isSelected ? "checked" : ""}
            aria-label="Sélectionner ${esc(row.acteur_nom) || row.groupe_id}"></sl-checkbox>
        </td>
        <td class="col-acteur">
          <a href="${safeHref(row.detail_url)}" target="_blank" rel="noreferrer"
            class="acteur-nom">${esc(row.acteur_nom) || "(sans nom)"}</a>
          <span class="acteur-id">${esc(row.acteur_id)}</span>
          <span class="acteur-statut">${esc(row.statut_display)}</span>
          ${parentBadge}
          ${errorNote}
        </td>
        ${cells}
      </tr>`
  }

  private renderCell(row: PivotRow, field: string): string {
    const cell = row.cells[field]
    if (!cell || (cell.current === null && cell.suggested === null)) {
      return `<td><span class="empty">—</span></td>`
    }
    const statut = cell.statut ?? STATUT_PENDING
    const stateClass = CELL_STATE_CLASS[statut] ?? "pending"
    const current =
      cell.current !== null && cell.current !== cell.suggested
        ? `<span class="old">${esc(cell.current)}</span>`
        : ""
    const suggested =
      cell.suggested !== null
        ? `<span class="new">${esc(cell.suggested)}</span>`
        : `<span class="empty">—</span>`
    return `<td class="sug ${stateClass}">
      ${current}${suggested}
      ${this.renderCellActions(row.groupe_id, field, statut)}
    </td>`
  }

  private renderCellActions(groupeId: number, field: string, statut: string): string {
    const button = (action: string, label: string, title: string) => `
      <button type="button" class="cell-action ${action}"
        data-cell-action="${action}" data-groupe-id="${groupeId}"
        data-field="${esc(field)}" title="${title}"
        aria-label="${title}"><span aria-hidden="true">${label}</span></button>`
    if (statut === STATUT_PENDING) {
      return `<span class="cell-actions">
        ${button("accept", "✓", `Accepter « ${esc(field)} »`)}
        ${button("reject", "✕", `Rejeter « ${esc(field)} »`)}
      </span>`
    }
    return `<span class="cell-actions">
      ${button("reset", "↺", "Annuler la décision")}
    </span>`
  }

  private renderBulkFieldOptions() {
    const options = this.fields
      .map(
        (field) => `<sl-option value="${esc(field.key)}">${esc(field.key)}</sl-option>`,
      )
      .join("")
    this.bulkFieldTarget.insertAdjacentHTML("beforeend", options)
  }

  private renderFieldToggles() {
    const buttons = this.fields
      .map(
        (field) => `
          <sl-button size="small" pill variant="primary"
            data-field-toggle="${esc(field.key)}">
            ${esc(field.key)}
          </sl-button>`,
      )
      .join("")
    this.fieldTogglesTarget.insertAdjacentHTML("beforeend", buttons)
    this.fieldTogglesTarget
      .querySelectorAll("[data-field-toggle]")
      .forEach((button) => {
        button.setAttribute("aria-pressed", "true")
        button.addEventListener("click", () => {
          const element = button as HTMLElement & { variant: string }
          const key = element.dataset.fieldToggle as string
          const column = this.table.getColumn(key)
          column?.toggleVisibility()
          const isVisible = column?.getIsVisible() !== false
          element.variant = isVisible ? "primary" : "default"
          element.setAttribute("aria-pressed", String(isVisible))
        })
      })
  }

  private renderStatus() {
    const selectedCount = this.selectedGroupeIds().length
    const isFilterScope = this.selectionScope === "filter"
    const selection = selectedCount
      ? ` · ${selectedCount} sélectionné${selectedCount > 1 ? "s" : ""}`
      : ""
    this.statusTarget.textContent = this.loading
      ? "Chargement…"
      : `${this.rows.length} chargés / ${this.total} acteurs${selection}`
    this.pagerInfoTarget.textContent = `${this.rows.length} acteurs chargés sur ${this.total}`
    this.loadMoreTarget.toggleAttribute("hidden", this.nextAfter === null)
    this.bulkBarTarget.toggleAttribute("hidden", selectedCount === 0 && !isFilterScope)
    if (isFilterScope) {
      const net = this.total - selectedCount
      this.bulkCountTarget.textContent = selectedCount
        ? `${net} acteurs filtrés (sauf ${selectedCount} cochés)`
        : `${this.total} (tous les acteurs filtrés)`
    } else {
      this.bulkCountTarget.textContent = String(selectedCount)
    }
    if (this.hasSelectFilteredTarget) {
      this.selectFilteredTarget.textContent = `Sélectionner les ${this.total} acteurs filtrés`
      this.selectFilteredTarget.toggleAttribute("hidden", isFilterScope)
    }
    this.updateSelectAllState(selectedCount)
    this.updateRowCount()
  }

  private updateSelectAllState(selectedCount: number) {
    const selectAll = this.headTarget.querySelector("[data-select-all]") as
      | (HTMLElement & { checked: boolean; indeterminate: boolean })
      | null
    if (!selectAll) {
      return
    }
    const allSelected = this.rows.length > 0 && selectedCount === this.rows.length
    selectAll.checked = allSelected
    selectAll.indeterminate = selectedCount > 0 && !allSelected
  }

  private updateRowCount() {
    // virtualization renders a window: aria-rowcount exposes the real size
    const table = this.scrollerTarget.querySelector("table")
    table?.setAttribute("aria-rowcount", String(this.total + 1))
    table?.setAttribute("aria-colcount", String(this.visibleFields().length + 2))
  }
}
