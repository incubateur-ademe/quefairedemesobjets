import posthog from "posthog-js"

const posthogConfig = {
  api_host: "https://eu.posthog.com",
  persistence: "memory",
}

if (process.env.NODE_ENV !== "development") {
  posthog.init("phc_SGbYOrenShCMKJOQYyl62se9ZqCHntjTlzgKNhrKnzm", posthogConfig)
} else {
  // TODO : ce serait bien qu'on définisse ces variables dans l'environnement de build,
  // pour qu'elles soient écrites durant cette phase et
  // avoir un environnement PostHog dédié en staging
  posthog.init("phc_SwcKewoXg9MZyAIdl8qsyvwz3Vij8Vlrbr2SjEeN3u9", posthogConfig)
  posthog.debug()
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

export default posthog
