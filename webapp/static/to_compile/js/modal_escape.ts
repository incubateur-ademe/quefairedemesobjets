// DSFR ignores Escape while the focus is on a form control, so a modal whose
// focus sits on a checkbox or a radio (after tabbing into it) never closes.
// Text fields keep Escape for themselves (autocomplete, native select popup).
const ESCAPE_IGNORED_BY_DSFR = 'input[type="checkbox"], input[type="radio"], label'

type DsfrApi = (element: Element) => { modal: { conceal: () => void } }

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !(event.target instanceof Element)) return
  if (!event.target.matches(ESCAPE_IGNORED_BY_DSFR)) return

  const modal = event.target.closest("dialog.fr-modal.fr-modal--opened")
  const dsfr = (window as unknown as { dsfr?: DsfrApi }).dsfr
  if (modal && dsfr) dsfr(modal).modal.conceal()
})
