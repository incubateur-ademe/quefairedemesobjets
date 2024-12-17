import { Controller } from "@hotwired/stimulus"
import { InteractionType as PosthogUIInteractionType, PosthogEventType } from "./types"
import posthog from "posthog-js"

export default class extends Controller<HTMLElement> {
  /**
  A Posthog user has some custom values that we set
  - The user informations : email, username, admin (or not)
  - If the page loads in an iframe
  - The conversion score : if a user executes a specific set of actions, we consider
    it as converted. For example : see a Produit page, interact with the map, etc...
  */
  declare readonly actionValue
  declare readonly posthogDebugValue
  declare readonly posthogKeyValue
  declare readonly userAdminValue
  declare readonly userConversionScoreValue
  declare readonly userEmailValue
  declare readonly userUsernameValue

  static values = {
    action: String,
    posthogDebug: Boolean,
    posthogKey: String,
    userAdmin: Boolean,
    userConversionScore: Number,
    userEmail: String,
    userUsername: String,
  }

  posthogConfig = {
    api_host: "https://eu.posthog.com",
    autocapture: false,
    capture_pageview: false,
    persistence: "memory",
  }

  userActionScore = {
    homePageView: 1,
    produitPageView: 1,
  }

  initialize(): void {
    posthog.init(this.posthogKeyValue, this.posthogConfig)
    this.#checkAuthenticatedUser()
    this.#checkIfWeAreInAnIframe()
    this.#fillSessionStorageWithAction()
    this.#setupIntersectionObserverForPageView()
    this.#captureUserConversionScore()
  }

  #fillSessionStorageWithAction() {
    if (this.actionValue) {
      sessionStorage.setItem(this.actionValue, "1")
    }
  }

  #checkAuthenticatedUser() {
    if (this.userUsernameValue) {
      posthog.identify(this.userUsernameValue, {
        email: this.userEmailValue,
        admin: this.userAdminValue,
      })
    }
  }

  #checkIfWeAreInAnIframe() {
    let areWeInAnIframe = false
    try {
      if (window.self !== window.top) {
        return true
      }
    } catch (e) {
      // Unable to access window.top
      // this might be due to cross-origin restrictions.
      // Assuming it's inside an iframe.
      return true
    }

    if (document.referrer) {
      return true
    }

    posthog.capture("$set", {
      $set: {
        iframe: areWeInAnIframe,
      },
    })
  }

  async #captureUserConversionScore() {
    // We allow a few seconds to ensure that the sesionstorage has been filled.
    // As it is not possible to listen on sessionStorage updates...
    setTimeout(() => {
      let conversionScore = 0
      for (const [key, value] of Object.entries(this.userActionScore)) {
        if (sessionStorage.getItem(key)) {
          conversionScore += value
        }
      }

      posthog.capture("$set", {
        $set: {
          conversionScore,
        },
      })
    }, 1000)
  }

  #setupIntersectionObserverForPageView() {
    const observer = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            posthog.capture("$pageview")
            observer.unobserve(entry.target)
          }
        })
      },
      {
        root: null,
        threshold: 0.01, // Trigger when at least 1% of the page is visible
      },
    )

    observer.observe(document.body)
  }

  // Sert principalement à typer les appels à la méthode capture de Posthog.
  // Ça évite d'appeler un événement indéfini, ce qui peut rapidement polluer
  // les données stockées côtés PostHog.
  // capture(posthogEvent: PosthogEventType, details: object) {
  //   posthog.capture(posthogEvent, details)
  // }
}
