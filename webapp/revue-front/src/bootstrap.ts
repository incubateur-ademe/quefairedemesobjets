/** Context rendered by the Django page (templates/data/revue.html). */
import { toSafeInternalHref } from "./safeHref"

export type Bootstrap = {
  basepath: string
  apiBase: string
  adminBase: string
  environment: string
  user: { id: number; username: string }
}

export function readBootstrap(doc: Document = document): Bootstrap {
  const element = doc.getElementById("revue-bootstrap")
  if (!element?.textContent) {
    throw new Error("Missing #revue-bootstrap data")
  }
  const parsed = JSON.parse(element.textContent) as Bootstrap
  return { ...parsed, basepath: toSafeInternalHref(parsed.basepath) }
}
