// DSFR ignores Escape while the focus is on a form field, so a modal whose
// focus sits on one (after tabbing into it) never closes. A field with an
// open suggestion list keeps Escape for itself.
type DsfrApi = (element: Element) => { modal: { conceal: () => void } }

function opener(modal: Element): HTMLElement | undefined {
  return [
    ...document.querySelectorAll<HTMLElement>(`[aria-controls="${modal.id}"]`),
  ].find((button) => button.checkVisibility({ checkVisibilityCSS: true }))
}

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !(event.target instanceof Element)) return
  if (!event.target.matches("input:not([aria-expanded='true'])")) return

  const modal = event.target.closest("dialog.fr-modal.fr-modal--opened")
  const dsfr = (window as unknown as { dsfr?: DsfrApi }).dsfr
  if (!modal || !dsfr) return

  dsfr(modal).modal.conceal()
  opener(modal)?.focus()
})
