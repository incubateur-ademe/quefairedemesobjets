import * as Turbo from "@hotwired/turbo"

function getCsrfToken(): string | null {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : null
}

export function getSharedData(element: HTMLElement): {
  fieldsValues: Record<string, any>
  fieldsGroups: string
  updateSuggestionUrl: string
} {
  const turboFrame = element.closest("turbo-frame") as HTMLElement | null
  if (!turboFrame) {
    throw new Error("No parent turbo-frame found")
  }
  return {
    fieldsValues: JSON.parse(turboFrame.dataset.fieldsValues || "{}"),
    fieldsGroups: turboFrame.dataset.fieldsGroups || "[]",
    updateSuggestionUrl: turboFrame.dataset.updateSuggestionUrl || "",
  }
}

export function postFieldsValues(
  element: HTMLElement,
  suggestionModele: string,
  fieldsValues: Record<string, any>,
  openedTab: string = "",
): void {
  const { fieldsGroups, updateSuggestionUrl } = getSharedData(element)
  if (!updateSuggestionUrl) {
    console.error("URL de mise à jour de la suggestion manquante")
    return
  }
  const formData = new FormData()
  formData.append("fields_values", JSON.stringify(fieldsValues))
  formData.append("fields_groups", fieldsGroups)
  formData.append("suggestion_modele", suggestionModele)
  if (openedTab) {
    formData.append("tab", openedTab)
  }
  postSuggestion(updateSuggestionUrl, formData)
}

export function postSuggestion(postUrl: string, formData: FormData): void {
  fetch(postUrl, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCsrfToken() ?? "",
      Accept: "text/vnd.turbo-stream.html",
    },
    body: formData,
    credentials: "same-origin",
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Échec de l'appel à la route ${postUrl} : (${response.status})`)
      }
      return response.text()
    })
    .then((html) => {
      Turbo.renderStreamMessage(html)
    })
    .catch((error) => {
      console.error(`Erreur lors de l'appel à la route ${postUrl} : ${error}`)
    })
}
