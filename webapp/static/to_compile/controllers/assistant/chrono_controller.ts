import { Controller } from "@hotwired/stimulus"

const THRESHOLD_MS = 50
const KEPT_TIMINGS = 8

type Timing = { server: number; total: number; places: number }

/**
 * Debug overlay: duration of the places requests.
 *
 * `server` comes from the `Server-Timing` header sent by the endpoint, so from
 * the time actually spent in the database. `total` includes the network and
 * the parsing: what the user feels.
 */
export default class extends Controller<HTMLElement> {
  static targets = ["value", "detail"]
  static values = { threshold: { type: Number, default: THRESHOLD_MS } }

  declare readonly valueTarget: HTMLElement
  declare readonly detailTarget: HTMLElement
  declare readonly hasDetailTarget: boolean
  declare thresholdValue: number

  private timings: Timing[] = []

  record(timing: Timing) {
    this.timings = [timing, ...this.timings].slice(0, KEPT_TIMINGS)
    this.#render()
  }

  #render() {
    const [last] = this.timings
    const median = this.#median(this.timings.map((timing) => timing.total))

    this.valueTarget.textContent = `${last.total.toFixed(0)} ms`
    this.element.dataset.overBudget = String(last.total > this.thresholdValue)

    if (this.hasDetailTarget) {
      this.detailTarget.textContent = [
        `serveur ${last.server.toFixed(1)} ms`,
        `médiane ${median.toFixed(0)} ms`,
        `${last.places} lieux`,
        `budget ${this.thresholdValue} ms`,
      ].join(" · ")
    }
  }

  #median(values: number[]): number {
    const sorted = [...values].sort((a, b) => a - b)
    return sorted[Math.floor(sorted.length / 2)] ?? 0
  }
}
