const dateTime = new Intl.DateTimeFormat("fr-FR", {
  dateStyle: "short",
  timeStyle: "short",
})
const number = new Intl.NumberFormat("fr-FR")

export const formatDateTime = (iso: string) => dateTime.format(new Date(iso))

export const formatNumber = (value: number) => number.format(value)

export const plural = (count: number, singular: string, pluralForm?: string) =>
  `${formatNumber(count)} ${count > 1 ? (pluralForm ?? `${singular}s`) : singular}`

/** ISO date (AAAA-MM-JJ) `days` days before `today`. */
export function daysAgo(days: number, today: Date = new Date()): string {
  const date = new Date(today)
  date.setDate(date.getDate() - days)
  return date.toISOString().slice(0, 10)
}
