export type BacklinkKey = "assistant" | "carte" | "formulaire"
export async function generateBackLink(iframe: HTMLIFrameElement, key: BacklinkKey) {
  if (!baseUrl) {
    console.error("Origin is not defined or is empty")
    return
  }

  const backlinkTag = document.createElement("div")
  backlinkTag.setAttribute(
    "style",
    "font-size: 0.9rem; text-align: center; padding-top: 0.5rem;",
  )

  let backlinkContent = ""

  try {
    const req = await fetch(`${origin}/embed/backlink?key=${key}`)
    backlinkContent = await req.text()
    backlinkTag.innerHTML = backlinkContent
    iframe.insertAdjacentElement("afterend", backlinkTag)
  } catch (exception) {
    console.log("Backlink impossible to load")
  }
}
