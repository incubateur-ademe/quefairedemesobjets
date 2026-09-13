import type { Lieu } from "./lieux_visibles"

export type CouleursPinpoint = {
  geste: string
  bonus: string
  adresse: string
}

/**
 * Élément DOM d'un pinpoint.
 *
 * La couleur suit le geste choisi par l'usager, pas une propriété du lieu :
 * un même acteur s'affiche en bleu si l'usager a choisi « donner » et en brun
 * s'il a choisi « revendre » (#3295). Seul le Bonus Réparation fait exception
 * et prend le pas sur la couleur du geste.
 */
export function elementPinpoint(
  lieu: Lieu,
  couleurs: CouleursPinpoint,
  geste: string,
): HTMLElement {
  const element = document.createElement("button")
  element.type = "button"
  element.className = "qfa-pinpoint"
  element.dataset.uuid = lieu.uuid
  element.dataset.geste = geste
  element.setAttribute("aria-label", lieu.nom)
  element.style.setProperty(
    "--qfa-pinpoint-couleur",
    lieu.bonus ? couleurs.bonus : couleurs.geste,
  )
  if (lieu.bonus) element.dataset.bonus = "true"

  const icone = document.createElement("span")
  icone.className = "qfa-pinpoint__icone"
  element.append(icone)
  return element
}

/**
 * Marqueur de l'adresse saisie par l'usager.
 *
 * N'est créé que pour une adresse précise, jamais pour une commune (#3356) :
 * « Lyon » n'a pas de position à montrer.
 */
export function elementAdresse(couleurs: CouleursPinpoint): HTMLElement {
  const element = document.createElement("div")
  element.className = "qfa-pinpoint qfa-pinpoint--adresse"
  element.setAttribute("role", "img")
  element.setAttribute("aria-label", "Votre adresse")
  element.style.setProperty("--qfa-pinpoint-couleur", couleurs.adresse)
  return element
}
