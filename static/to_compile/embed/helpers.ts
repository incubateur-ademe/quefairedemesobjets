export type BacklinkKey = "assistant" | "carte" | "formulaire"
export async function generateBackLink(iframe: HTMLIFrameElement, key: BacklinkKey) {
  const backlinkTag = document.createElement("div")
  backlinkTag.setAttribute(
    "style",
    "font-size: 0.9rem; text-align: center; padding-top: 0.5rem;",
  )
  // TODO: get backlink content
  const backlinkContent = await fetch(`${origin}/embed/backlink?key=${key}`)
  backlinkTag.innerHTML = await backlinkContent.text()
  iframe.insertAdjacentElement("afterend", backlinkTag)
}
