import http from "k6/http"

import { check, sleep } from "k6"

export const options = {
    // vus: 10,
    // duration: "30s",
    stages: [
        { duration: "1m", target: 20 },
        { duration: "1m", target: 40 },
        { duration: "1m", target: 80 },
        { duration: "1m", target: 40 },
        { duration: "1m", target: 20 },
        { duration: "1m", target: 0 },
    ],
}

export default function () {
    // https://longuevieauxobjets.ademe.fr/?r=76&direction=jecherche&action_list=&sous_categorie_objet=V%C3%A9lo&adresse=10+Rue+de+Gess%C3%A9+93200+Saint-Denis&longitude=2.349562&latitude=48.940018&digital=&preter=on&mettreenlocation=on&reparer=on&donner=on&echanger=on&revendre=on&emprunter=on&louer=on&echanger=on&acheter=on#solutions
    // https://longuevieauxobjets.ademe.fr/?r=76&direction=jecherche&longitude=2.349562&latitude=48.940018
    let directionOptions = ["jai", "jecherche"]
    let directionIndex = Math.floor(Math.random() * directionOptions.length)
    let direction = directionOptions[directionIndex]
    let longitude = 6 * Math.random()
    let latitude = 44 + 5 * Math.random()
    let myUrlWithParams = `https://longuevieauxobjets.ademe.fr/?r=${Math.floor(
        Math.random() * 100,
    )}&direction=${direction}&longitude=${longitude}&latitude=${latitude}&adresse=fake+adresse`

    const res = http.get(myUrlWithParams)

    check(res, { "status was 200": (r) => r.status == 200 })
    sleep(10 * Math.random())
}
