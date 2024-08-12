import posthog from "posthog-js"
import { InteractionType } from "./types"

const posthogConfig = {
  api_host: "https://eu.posthog.com",
  persistence: "memory",
}

if (process.env.NODE_ENV !== "development") {
  posthog.init("phc_SGbYOrenShCMKJOQYyl62se9ZqCHntjTlzgKNhrKnzm", posthogConfig)
} else {
  posthog.init("phc_SwcKewoXg9MZyAIdl8qsyvwz3Vij8Vlrbr2SjEeN3u9", posthogConfig)
}

window.addEventListener("DOMContentLoaded", () => {
  const user = document.querySelector<HTMLScriptElement>("#posthog-user")
  if (user) {
    // Le contenu de #posthog-user n'étant rendu que pour
    // les utilisateurs authentifiés, sa présence garantit qu'il
    // ait bien du contenu.
    const userData = user?.textContent!
    const { email, admin, iframe, username } = JSON.parse(userData)
    posthog.identify(username, {
      email: email,
      admin: admin,
      iframe: iframe,
    })
  }

  const infos = document.querySelector<HTMLScriptElement>("#posthog-infos")?.textContent!
  const { iframe } = JSON.parse(infos)
  posthog.capture("$set", {
    $set: {
      iframe
    }
  })
})

export function captureInteractionWithASolution(
    specificInteractionType?: InteractionType,
) {
    posthog.capture("interaction_with_a_solution", {
        specific_interaction_type: specificInteractionType,
    })
}

export default posthog
