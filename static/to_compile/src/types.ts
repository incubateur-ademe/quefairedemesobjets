export interface Location {
    geometry?: {
        coordinates: number[]
    }
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
    adresse: string
    adresse_complement: string
    code_postal: string
    ville: string
    url: string
    proposition_services: Array<PropositionService>
    location: ActorLocation
    /*
        Other fields:
            identifiant_unique
            email
            telephone
            multi_base
            nom_commercial
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
        this.adresse = actor_fields["adresse"]
        this.adresse_complement = actor_fields["adresse_complement"]
        this.code_postal = actor_fields["code_postal"]
        this.ville = actor_fields["ville"]
        this.url = actor_fields["url"]
        this.proposition_services = actor_fields["proposition_services"]
        this.location = actor_fields["location"]
    }

    popupTitle(): string {
        return "<p><strong>" + this.nom + "</strong></b><br>"
    }

    popupContent(): string {
        let popupContent = ""
        let services = Array.from(
            new Set(
                this.proposition_services.map((proposition_service) => {
                    return proposition_service.acteur_service.nom
                }),
            ),
        )

        popupContent += services.join("<br>")
        popupContent += "<br><br>"
        if (this.adresse !== "") {
            popupContent += this.adresse + "<br>"
        }
        if (this.adresse_complement !== "") {
            popupContent += this.adresse_complement + "<br>"
        }
        if (this.code_postal !== "") {
            popupContent += this.code_postal + " "
        }
        if (this.ville !== "") {
            popupContent += this.ville + "<br>"
        }
        if (this.url !== "") {
            popupContent +=
                "<a href='" + this.url + "' target='_blank'>" + this.url + "</a><br>"
        }

        return popupContent
    }
}
