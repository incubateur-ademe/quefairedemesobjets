/** Jest replacement of src/wa.ts: plain custom elements, no Lit rendering. */
import { createElement, forwardRef, type ReactNode } from "react"

type Props = Record<string, unknown> & { children?: ReactNode }

function make(tag: string) {
  const Component = forwardRef<HTMLElement, Props>(({ children, ...props }, ref) =>
    createElement(
      tag,
      { ...props, ref } as Record<string, unknown>,
      children as ReactNode,
    ),
  )
  Component.displayName = tag
  return Component
}

export const WaBadge = make("wa-badge")
export const WaButton = make("wa-button")
export const WaCallout = make("wa-callout")
export const WaCheckbox = make("wa-checkbox")
export const WaDetails = make("wa-details")
export const WaDialog = make("wa-dialog")
export const WaDrawer = make("wa-drawer")
export const WaIcon = make("wa-icon")
export const WaInput = make("wa-input")
export const WaOption = make("wa-option")
export const WaSelect = make("wa-select")
export const WaSpinner = make("wa-spinner")
export const WaTooltip = make("wa-tooltip")
