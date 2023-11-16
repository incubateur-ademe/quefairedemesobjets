import http from "k6/http"

import { check, sleep } from "k6"

export const options = {
    // vus: 10,
    // duration: "30s",
    stages: [
        { duration: "5m", target: 1000 },
        { duration: "10m", target: 1000 },
        { duration: "5m", target: 0 },
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
    let tagName = "GetSolutions"
    let myUrlWithParams = `https://longuevieauxobjets.ademe.fr/?r=${Math.floor(
        Math.random() * 100,
    )}&direction=${direction}&longitude=${longitude}&latitude=${latitude}&adresse=fake+adresse`

    if (Math.random() > 0.5) {
        myUrlWithParams += "&digital=1"
        tagName += "Digital"
    } else {
        myUrlWithParams += "&digital=0"
    }
    if (Math.random() > 0.5) {
        myUrlWithParams += "&label_reparacteur=on"
        tagName += "WithReparActeur"
    }
    if (Math.random() > 0.3) {
        let objetOptions = [
            "Accessoire automobile (et deux-roues) électronique",
            "Détecteur radar",
            "Radar de stationnement",
            "Allume-cigare",
            "Aiguille usagée (médicale)",
            "Aiguille à stylo",
            "Aiguille de transfert",
            "Aiguille seule (médicale)",
            "Appareil photo jetable",
            "Appareil photo",
            "Appareil photo numérique",
            "Articles en cuir (hors chaussures)",
            "Ceinture en cuir",
            "Gants en cuir",
            "Portefeuille en cuir",
            "Sacoche en cuir",
            "Sac à main en cuir",
            "Maroquinerie",
            "Blouson en cuir",
            "Pantalon en cuir",
            "Bracelet en cuir",
            "Aspirateur",
            "Equipement d'entretien",
            "Autoradio",
            "Radio",
            "Baladeur",
            "Walkman",
            "MP3",
            "Batterie (hors batterie de voiture)",
            "Accumulateur",
            "Biberon en plastique",
            "Biberon",
            "Bijou fantaisie (accessoires de mode)",
            "Bodyboard",
            "Surf",
            "Bottes en caoutchouc",
            "Bottes de pluie",
            "Bottes de pêche",
            "Bougie en cire",
            "Chandelle",
            "Cierge",
            "Bougie",
            "Bouteille de plongée",
            "Canapé",
            "Canapé-lit",
            "Carte RFID",
            "Clé RFID",
            "Carte à puce (bancaire, de téléphone, d'identité)",
            "Cartouche d'impression (à jet d'encre, laser)",
            "Casque",
            "Cathéter",
            "Cathéter tout en un",
            "CD/DVD, cassette (avec ou sans boîtier)",
            "Blu-ray",
        ]
        let objetIndex = Math.floor(Math.random() * objetOptions.length)
        let objet = objetOptions[objetIndex]
        myUrlWithParams += `&sous_categorie_objet=${encodeURI(objet)}`
        tagName += "WithSousCat"
    }

    if (Math.random() > 0.5 && direction == "jecherche") {
        let action1 = Math.random() > 0.5 ? "emprunter" : "louer"
        let action2 = Math.random() > 0.5 ? "acheter" : "echanger"
        myUrlWithParams += `&action_list=${action1}|${action2}`
        tagName += "WithAction"
    }
    if (Math.random() > 0.5 && direction == "jai") {
        let action1 = Math.random() > 0.5 ? "donner" : "echanger"
        let action2 = Math.random() > 0.5 ? "revendre" : "mettreenlocation"
        myUrlWithParams += `&action_list=${action1}|${action2}`
        tagName += "WithAction"
    }

    const res = http.get(myUrlWithParams, {
        tags: { name: tagName },
    })

    check(res, { "status was 200": (r) => r.status == 200 })
    sleep(10 * Math.random())
}
