import { useAnnuaireEntreprise } from "../../api/queries"
import type { AnnuaireEntreprise, GroupeDetail, Identifiant } from "../../api/types"
import { ExternalLink } from "../../components/common/Value"
import { nafLabel } from "../../domain/naf"
import { WaSpinner } from "../../wa"

const CHAMPS = [
  ["siret", "SIRET"],
  ["siren", "SIREN"],
] as const

/** For each SIRET / SIREN of the groupe (corrected value, then parent, correction
 * and acteur importé when they differ), the entreprise and the établissement
 * found in the Annuaire des entreprises. */
export function AnnuaireTab({ groupe }: { groupe: GroupeDetail }) {
  return (
    <div className="annuaire">
      {CHAMPS.map(([champ, titre]) => (
        <section key={champ}>
          <h3>{titre}</h3>
          {groupe.annuaire[champ].length === 0 ? (
            <p className="inherit">aucun {titre}</p>
          ) : (
            groupe.annuaire[champ].map((identifiant) => (
              <IdentifiantCard
                key={identifiant.source}
                champ={champ}
                identifiant={identifiant}
              />
            ))
          )}
        </section>
      ))}
    </div>
  )
}

function IdentifiantCard({
  champ,
  identifiant,
}: {
  champ: "siret" | "siren"
  identifiant: Identifiant
}) {
  const annuaire = useAnnuaireEntreprise(champ, identifiant.valeur)
  return (
    <div className="ae-card">
      <div className="ae-card__head">
        <span className="ae-source">{identifiant.label}</span>
        {identifiant.propose && <span className="pill p-accent">proposé</span>}
        <span className="val">{identifiant.valeur}</span>
        <ExternalLink value={identifiant.valeur} />
        {annuaire.isFetching && <WaSpinner />}
      </div>
      {annuaire.error && <p className="error">{annuaire.error.message}</p>}
      {annuaire.data && <AnnuaireResult champ={champ} result={annuaire.data} />}
    </div>
  )
}

function AnnuaireResult({
  champ,
  result,
}: {
  champ: "siret" | "siren"
  result: AnnuaireEntreprise
}) {
  if (!result.entreprise) {
    return <p className="ae-ferme">Introuvable dans l’Annuaire des entreprises</p>
  }
  return (
    <dl className="kgrid">
      <Bloc
        titre="Entreprise"
        nom={result.entreprise.nom}
        adresse={result.entreprise.adresse}
        activite={result.entreprise.activite_code}
        etat={result.entreprise.etat}
      />
      {champ === "siret" &&
        (result.etablissement ? (
          <Bloc
            titre={
              result.etablissement.est_siege ? "Établissement (siège)" : "Établissement"
            }
            nom={result.etablissement.nom}
            adresse={result.etablissement.adresse}
            activite={result.etablissement.activite_code}
            etat={result.etablissement.etat === "ferme" ? "fermé" : "actif"}
          />
        ) : (
          <div className="kgrid__item">
            <dt>Établissement</dt>
            <dd className="ae-ferme">introuvable dans cette entreprise</dd>
          </div>
        ))}
    </dl>
  )
}

function Bloc({
  titre,
  nom,
  adresse,
  activite,
  etat,
}: {
  titre: string
  nom: string
  adresse: string
  activite: string
  /** État administratif: « actif », else « inactif » or « fermé » */
  etat: string
}) {
  const label = nafLabel(activite)
  return (
    <div className="kgrid__item">
      <dt>{titre}</dt>
      <dd>
        <div className="ae-nom">
          {nom || <span className="inherit">nom non diffusé</span>}
        </div>
        <div>
          État administratif :{" "}
          <span className={`pill ${etat === "actif" ? "p-ok" : "p-danger"}`}>
            {etat}
          </span>
        </div>
        <div>{adresse || <span className="inherit">adresse non diffusée</span>}</div>
        <div className="muted">
          {activite ? (
            <>
              <span className="mono">{activite}</span>
              {label ? ` · ${label}` : ""}
            </>
          ) : (
            <span className="inherit">activité inconnue</span>
          )}
        </div>
      </dd>
    </div>
  )
}
