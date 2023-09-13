export interface Location {
    latitude?: number
    longitude?: number
}

export interface ActorLocation {
    coordinates: number[]
}

export interface ActeurService {
    nom: string
}

export interface Action {
    nom: string
}

export interface PropositionService {
    acteur_service: ActeurService
    action: Action
}

export class Actor {
    id: number
    nom: string
    nom_commercial: string
    adresse: string
    adresse_complement: string
    code_postal: string
    ville: string
    url: string
    telephone: string
    proposition_services: Array<PropositionService>
    location: ActorLocation
    /*
        Other fields:
            identifiant_unique
            email
            telephone
            multi_base
            nom_officiel
            manuel
            label_reparacteur
            siret
            source_donnee
            identifiant_externe
            acteur_type
            acteur_service
            sous_categories
    */

    constructor(actor_fields: object) {
        this.id = actor_fields["id"]
        this.nom = actor_fields["nom"]
        this.nom_commercial = actor_fields["nom_commercial"]
        this.adresse = actor_fields["adresse"]
        this.adresse_complement = actor_fields["adresse_complement"]
        this.code_postal = actor_fields["code_postal"]
        this.ville = actor_fields["ville"]
        this.telephone = actor_fields["telephone"]
        this.url = actor_fields["url"]
        this.proposition_services = actor_fields["proposition_services"]
        this.location = actor_fields["location"]
    }

    popupTitle(): string {
        let title: string = this.nom_commercial || this.nom
        let title_html = document.createElement("h5")
        title_html.className = "fr-mb-0"
        title_html.innerHTML = title
        return title_html.outerHTML
    }

    popupContent(): string {
        let popup = document.createElement("div")
        let popupContent = ""
        if (this.proposition_services !== undefined) {
            let services = Array.from(
                new Set(
                    this.proposition_services.map((proposition_service) => {
                        return proposition_service.acteur_service.nom
                    }),
                ),
            )

            popupContent += services.join("<br>")
            popupContent += "<br><br>"
        }
        if (this.adresse) {
            popupContent += this.adresse + "<br>"
        }
        if (this.adresse_complement) {
            popupContent += this.adresse_complement + "<br>"
        }
        if (this.code_postal) {
            popupContent += this.code_postal + " "
        }
        if (this.ville) {
            popupContent += this.ville + "<br>"
        }
        if (this.telephone) {
            popupContent += this.telephone + "<br>"
        }
        popup.innerHTML = popupContent
        if (this.url) {
            let url = document.createElement("a")
            url.href = this.url
            url.target = "_blank"
            url.innerHTML = this.url
            popup.appendChild(url)
        }

        return popup.outerHTML
    }
}
