import { Controller } from "@hotwired/stimulus"

const API_BASE = "https://api.annuaire-entreprises.data.gouv.fr/v3"
const FETCH_TIMEOUT_MS = 8000

type EntreeType = "etablissement" | "unite_legale"

interface Entree {
  label: string
  type: EntreeType
  value: string
}

interface StatutResult {
  entree: Entree
  etat_administratif: string | null
  error: boolean
}

function formatEtat(type: EntreeType, etat: string): string {
  if (type === "etablissement") {
    if (etat === "A") return "Actif"
    if (etat === "F") return "Fermé"
  } else {
    if (etat === "A") return "Active"
    if (etat === "C") return "Cessée"
  }
  return etat
}

export default class extends Controller<HTMLElement> {
  static values = {
    entrees: { type: Array, default: [] },
  }
  static targets = ["container"]

  declare readonly entreesValue: Entree[]
  declare readonly containerTarget: HTMLElement

  connect() {
    this.containerTarget.innerHTML =
      '<p class="qf-text-gray-500 qf-italic">Chargement des données annuaire entreprise\u2026</p>'
    setTimeout(() => this.fetchAll(), 0)
  }

  async fetchAll() {
    if (this.entreesValue.length === 0) {
      this.containerTarget.innerHTML =
        '<p class="qf-text-gray-500">Aucun SIRET ou SIREN à vérifier.</p>'
      return
    }

    const settled = await Promise.allSettled(
      this.entreesValue.map((entree) => this.fetchEntree(entree)),
    )

    const items: StatutResult[] = settled.map((result, i) => {
      if (result.status === "fulfilled") return result.value
      return { entree: this.entreesValue[i], etat_administratif: null, error: true }
    })

    this.renderResults(items)
  }

  async fetchEntree(entree: Entree): Promise<StatutResult> {
    const url =
      entree.type === "etablissement"
        ? `${API_BASE}/etablissements/${entree.value}`
        : `${API_BASE}/unites_legales/${entree.value}`

    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)

    try {
      const response = await fetch(url, { signal: controller.signal })
      clearTimeout(timer)
      if (!response.ok) {
        return { entree, etat_administratif: null, error: true }
      }
      const data = await response.json()
      const etat: string | null = data.etat_administratif ?? null
      return { entree, etat_administratif: etat, error: false }
    } catch {
      clearTimeout(timer)
      return { entree, etat_administratif: null, error: true }
    }
  }

  renderResults(items: StatutResult[]) {
    const rows = items
      .map(({ entree, etat_administratif, error }) => {
        const typeLabel =
          entree.type === "etablissement" ? "Établissement" : "Unité légale"
        const codeLabel =
          entree.type === "etablissement"
            ? `SIRET\u00a0: ${entree.value}`
            : `SIREN\u00a0: ${entree.value}`

        let statusHtml: string
        if (error || etat_administratif === null) {
          statusHtml = '<span class="qf-text-gray-500">Non disponible</span>'
        } else {
          const isActif = etat_administratif === "A"
          const colorClass = isActif ? "qf-text-green-600" : "qf-text-red-600"
          statusHtml = `<span class="${colorClass}">${formatEtat(entree.type, etat_administratif)}</span>`
        }

        return `<tr>
          <td class="qf-pr-4 qf-py-1">${entree.label}</td>
          <td class="qf-pr-4 qf-py-1">${typeLabel}</td>
          <td class="qf-pr-4 qf-py-1 qf-font-mono">${codeLabel}</td>
          <td class="qf-py-1">${statusHtml}</td>
        </tr>`
      })
      .join("")

    this.containerTarget.innerHTML = `
      <table class="qf-w-full qf-text-sm">
        <thead>
          <tr class="qf-text-left">
            <th class="qf-pr-4 qf-pb-2 qf-font-semibold">Source</th>
            <th class="qf-pr-4 qf-pb-2 qf-font-semibold">Type</th>
            <th class="qf-pr-4 qf-pb-2 qf-font-semibold">Identifiant</th>
            <th class="qf-pb-2 qf-font-semibold">État administratif</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`
  }
}
