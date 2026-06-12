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

const STATUT_PENDING = "AVALIDER"
const STATUT_ACCEPTED = "ATRAITER"
const STATUT_REJECTED = "REJETEE"

const CELL_STATE_CLASS: Record<string, string> = {
  [STATUT_PENDING]: "pending",
  [STATUT_ACCEPTED]: "accepted",
  [STATUT_REJECTED]: "rejected",
}

function esc(value: string | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return ""
  }
  const div = document.createElement("div")
  div.textContent = value
  return div.innerHTML
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
  ]
  static values = {
    rowsUrl: String,
    bulkUrl: String,
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
  declare readonly rowsUrlValue: string
  declare readonly bulkUrlValue: string
  declare readonly csrfValue: string

  private rows: PivotRow[] = []
  private fields: FieldMeta[] = []
  private total = 0
  private nextAfter: number | null = 0
  private loading = false
  private q = ""
  private statutFilter = "AVALIDER"
  private searchDebounce: number | undefined
  private table!: Table<PivotRow>
  private tableState!: TableState
  private virtualizer!: Virtualizer<HTMLDivElement, HTMLTableRowElement>
  private cleanupVirtualizer: () => void = () => {}

  connect() {
    this.initTable()
    this.initVirtualizer()
    // Cell action buttons are re-rendered on every scroll: one delegated
    // listener survives instead of re-binding per render.
    this.bodyTarget.addEventListener("click", (event) => this.onCellAction(event))
    this.fetchRows()
  }

  disconnect() {
    this.cleanupVirtualizer()
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
      this.resetAndFetch()
    }, 300)
  }

  onStatutChange() {
    this.statutFilter = this.statutFilterTarget.value || "AVALIDER"
    this.resetAndFetch()
  }

  private resetAndFetch() {
    this.rows = []
    this.total = 0
    this.nextAfter = 0
    this.table.resetRowSelection(true)
    this.table.setOptions((prev) => ({ ...prev, data: this.rows }))
    this.virtualizer.setOptions({ ...this.virtualizer.options, count: 0 })
    this.scrollerTarget.scrollTop = 0
    this.renderAll()
    this.fetchRows()
  }

  // --- mutations (per-cell and bulk accept/reject) ---

  bulkAccept() {
    this.postBulk(this.selectedGroupeIds(), this.bulkFieldTarget.value, "accept")
  }

  bulkReject() {
    this.postBulk(this.selectedGroupeIds(), this.bulkFieldTarget.value, "reject")
  }

  clearSelection() {
    this.table.toggleAllRowsSelected(false)
  }

  private onCellAction(event: Event) {
    const button = (event.target as HTMLElement).closest<HTMLElement>(
      "[data-cell-action]",
    )
    if (!button) {
      return
    }
    event.preventDefault()
    this.postBulk(
      [Number(button.dataset.groupeId)],
      button.dataset.field ?? "",
      button.dataset.cellAction as string,
    )
  }

  private selectedGroupeIds(): number[] {
    return Object.entries(this.tableState.rowSelection ?? {})
      .filter(([, isSelected]) => isSelected)
      .map(([groupeId]) => Number(groupeId))
  }

  private async postBulk(groupeIds: number[], champ: string, action: string) {
    if (!groupeIds.length || this.loading) {
      return
    }
    this.loading = true
    this.renderStatus()
    try {
      const response = await fetch(this.bulkUrlValue, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.csrfValue,
          Accept: "application/json",
        },
        credentials: "same-origin",
        body: JSON.stringify({
          groupe_ids: groupeIds,
          champ: champ || null,
          action,
        }),
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const payload = await response.json()
      this.mergeRows(payload.rows as PivotRow[])
      this.fields = this.mergeFieldsMeta(payload.meta.fields as FieldMeta[])
      this.renderAll()
    } catch (error) {
      this.statusTarget.textContent = `Erreur lors de l'action (${error})`
    } finally {
      this.loading = false
      this.renderStatus()
    }
  }

  private mergeRows(updatedRows: PivotRow[]) {
    const byId = new Map(updatedRows.map((row) => [row.groupe_id, row]))
    this.rows = this.rows.map((row) => byId.get(row.groupe_id) ?? row)
    this.table.setOptions((prev) => ({ ...prev, data: this.rows }))
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
    this.tableState = {
      columnVisibility: {},
      rowSelection: {},
    } as TableState

    this.table = createTable<PivotRow>({
      data: [],
      columns: [],
      state: this.tableState,
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
    this.renderHead()
    this.renderBody()
    this.renderStatus()
  }

  private renderHead() {
    const fieldHeads = this.visibleFields()
      .map(
        (field) => `
          <th scope="col">
            ${esc(field.key)}
            <sl-badge variant="warning" pill>${field.pending}</sl-badge>
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
    this.headTarget
      .querySelector("[data-select-all]")
      ?.addEventListener("sl-change", (event) => {
        const checked = (event.target as HTMLInputElement).checked
        this.table.toggleAllRowsSelected(checked)
      })
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
      .map((virtualItem) => this.renderRow(this.rows[virtualItem.index]))
      .join("")

    this.bodyTarget.innerHTML = `
      ${this.spacerRow(paddingTop, columnCount)}
      ${renderedRows}
      ${this.spacerRow(paddingBottom, columnCount)}`

    this.bodyTarget.querySelectorAll("[data-row-select]").forEach((checkbox) => {
      checkbox.addEventListener("sl-change", (event) => {
        const target = event.target as HTMLElement & { checked: boolean }
        const rowId = target.dataset.rowSelect as string
        this.table.getRow(rowId).toggleSelected(target.checked)
      })
    })

    const lastIndex = virtualItems[virtualItems.length - 1].index
    if (lastIndex >= this.rows.length - LOAD_MORE_THRESHOLD) {
      this.fetchRows()
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

  private renderRow(row: PivotRow): string {
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
      <tr class="${isSelected ? "selected" : ""}" data-groupe-id="${row.groupe_id}">
        <td class="col-select">
          <sl-checkbox size="small" data-row-select="${row.groupe_id}"
            ${isSelected ? "checked" : ""}
            aria-label="Sélectionner ${esc(row.acteur_nom) || row.groupe_id}"></sl-checkbox>
        </td>
        <td class="col-acteur">
          <a href="${esc(row.detail_url)}" target="_blank" rel="noreferrer"
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
        data-field="${esc(field)}" title="${title}">${label}</button>`
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
        button.addEventListener("click", () => {
          const element = button as HTMLElement & { variant: string }
          const key = element.dataset.fieldToggle as string
          const column = this.table.getColumn(key)
          column?.toggleVisibility()
          element.variant = column?.getIsVisible() === false ? "default" : "primary"
        })
      })
  }

  private renderStatus() {
    const selectedCount = this.selectedGroupeIds().length
    const selection = selectedCount
      ? ` · ${selectedCount} sélectionné${selectedCount > 1 ? "s" : ""}`
      : ""
    this.statusTarget.textContent = this.loading
      ? "Chargement…"
      : `${this.rows.length} chargés / ${this.total} acteurs${selection}`
    this.pagerInfoTarget.textContent = `${this.rows.length} acteurs chargés sur ${this.total}`
    this.loadMoreTarget.toggleAttribute("hidden", this.nextAfter === null)
    this.bulkBarTarget.toggleAttribute("hidden", selectedCount === 0)
    this.bulkCountTarget.textContent = String(selectedCount)
  }
}
