/** Local icon library (Remix Icon): no icon is fetched from a CDN. Icons are
 * inlined in the bundle as data URLs, only those listed here. */
import { registerIconLibrary } from "@awesome.me/webawesome/dist/webawesome.js"
import alert from "data-url:remixicon/icons/System/alert-line.svg"
import arrowLeft from "data-url:remixicon/icons/Arrows/arrow-left-s-line.svg"
import arrowRight from "data-url:remixicon/icons/Arrows/arrow-right-s-line.svg"
import check from "data-url:remixicon/icons/System/check-line.svg"
import close from "data-url:remixicon/icons/System/close-line.svg"
import deleteBin from "data-url:remixicon/icons/System/delete-bin-line.svg"
import errorWarning from "data-url:remixicon/icons/System/error-warning-line.svg"
import externalLink from "data-url:remixicon/icons/System/external-link-line.svg"
import fileList from "data-url:remixicon/icons/Document/file-list-line.svg"
import filter from "data-url:remixicon/icons/System/filter-line.svg"
import information from "data-url:remixicon/icons/System/information-line.svg"

export const ICONS: Record<string, string> = {
  alert,
  "arrow-left": arrowLeft,
  "arrow-right": arrowRight,
  check,
  close,
  "delete-bin": deleteBin,
  "error-warning": errorWarning,
  "external-link": externalLink,
  "file-list": fileList,
  filter,
  information,
}

export type IconName = keyof typeof ICONS

export function registerIcons() {
  registerIconLibrary("default", {
    resolver: (name) => ICONS[name] ?? "",
    mutator: (svg) => svg.setAttribute("fill", "currentColor"),
  })
}
