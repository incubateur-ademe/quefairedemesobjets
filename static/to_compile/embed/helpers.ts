export type BacklinkKey = "assistant" | "carte" | "formulaire"
export async function generateBackLink(
  iframe: HTMLIFrameElement,
  key: BacklinkKey,
  baseUrl: string,
) {
  const backlinkTag = document.createElement("div")
  backlinkTag.setAttribute(
    "style",
    "font-family: system-ui !important; font-size: 0.9rem; text-align: center; padding-top: 0.5rem;",
  )
  let backlinkContent = ""
  try {
    const req = await fetch(`${baseUrl}/embed/backlink?key=${key}`)
    backlinkContent = await req.text()
    backlinkTag.innerHTML = backlinkContent
    iframe.insertAdjacentElement("afterend", backlinkTag)
  } catch (exception) {
    console.log("Backlink impossible to load")
  }
}
