export type BacklinkKey =
  | "assistant"
  | "carte"
  | "formulaire"
  | "infotri"
  | "infotri-configurator"
export async function generateBackLink(
  iframe: HTMLIFrameElement,
  key: BacklinkKey,
  baseUrl?: string | null,
  style = "font-family: system-ui; font-size: 0.9rem; text-align: center; padding-top: 0.5rem;",
) {
  if (!baseUrl) {
    console.error("Origin is not defined or is empty")
    return
  }

  const backlinkTag = document.createElement("div")
  backlinkTag.setAttribute("style", style)

  let backlinkContent = ""
  try {
    const req = await fetch(`${baseUrl}/embed/backlink?key=${key}`)
    backlinkContent = await req.text()
    backlinkTag.innerHTML = backlinkContent

    // Wrap iframe with backlink container
    const wrapper = document.createElement("div")
    const backlinkLink = backlinkTag.querySelector("a")

    if (backlinkLink) {
      // Remove text decoration from link style
      backlinkLink.setAttribute("style", "display: block; text-decoration: none;")

      // Insert iframe inside the link
      iframe.parentNode?.insertBefore(wrapper, iframe)
      backlinkLink.appendChild(iframe)
      wrapper.appendChild(backlinkTag)
    } else {
      // Fallback: insert after iframe if no link found
      iframe.insertAdjacentElement("afterend", backlinkTag)
    }
  } catch (exception) {
    console.log("Backlink impossible to load")
  }
}
