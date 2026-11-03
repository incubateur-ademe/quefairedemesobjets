/**
 * Host-page scrolling for an iframe asking to be brought to the top (a new
 * assistant screen): the host's fixed or sticky header must not cover it.
 *
 * Nothing is assumed about the host site: what is actually pinned to the top
 * of the viewport is measured, before and after scrolling, since some headers
 * change size with the scroll direction.
 */

const MARGIN = 16
const TOLERANCE = 2
/** The iframe top is left alone when it already sits in this upper share. */
const VISIBLE_SHARE = 0.4
const POLL_MS = 50
const SETTLED_MS = 300
const MAX_PASSES = 3

/** Height of the viewport top covered by fixed or sticky elements. */
export function coveredHeight(iframe: HTMLElement): number {
  let bottom = 0
  for (const share of [0.1, 0.5, 0.9]) {
    for (const element of document.elementsFromPoint(window.innerWidth * share, 1)) {
      // The iframe and its containers do not cover themselves.
      if (element.contains(iframe)) continue
      for (let node: Element | null = element; node; node = node.parentElement) {
        const { position } = getComputedStyle(node)
        if (position === "fixed" || position === "sticky") {
          bottom = Math.max(bottom, node.getBoundingClientRect().bottom)
        }
      }
    }
  }
  return bottom
}

function offsetFromTarget(iframe: HTMLElement): number {
  return iframe.getBoundingClientRect().top - (coveredHeight(iframe) + MARGIN)
}

function whenSettled(callback: () => void) {
  let lastY = window.scrollY
  let stillFor = 0
  const timer = setInterval(() => {
    stillFor = window.scrollY === lastY ? stillFor + POLL_MS : 0
    lastY = window.scrollY
    if (stillFor < SETTLED_MS) return
    clearInterval(timer)
    callback()
  }, POLL_MS)
}

function scrollBy(iframe: HTMLElement, pass: number) {
  const offset = offsetFromTarget(iframe)
  if (Math.abs(offset) <= TOLERANCE || pass > MAX_PASSES) return
  window.scrollTo({ top: window.scrollY + offset, behavior: "smooth" })
  // The header may still be animating: measure again once the page is still.
  whenSettled(() => scrollBy(iframe, pass + 1))
}

/** iframe-resizer `onScroll`: returns false, the page is scrolled here. */
export function scrollIframeIntoView(iframe: HTMLElement): boolean {
  const { top } = iframe.getBoundingClientRect()
  const isVisible =
    top >= coveredHeight(iframe) && top <= window.innerHeight * VISIBLE_SHARE
  if (!isVisible) scrollBy(iframe, 1)
  return false
}
