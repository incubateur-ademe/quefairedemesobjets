import { useState } from "react"

import type { GroupeActions } from "../../api/mutations"
import { useAnnuaireEntreprise, useGroupeDetail } from "../../api/queries"
import type { GroupeDetail, Identifiant, Modele, Policy } from "../../api/types"
import { StatutPill } from "../../components/common/Pill"
import {
  WaButton,
  WaDialog,
  WaIcon,
  WaSpinner,
  WaTab,
  WaTabGroup,
  WaTabPanel,
} from "../../wa"
import type { ModalTab } from "../cohorte/GroupesView"
import { AnnuaireTab } from "./AnnuaireTab"
import {
  LocalisationMap,
  MARKERS,
  type MapPoint,
  type MarkerKey,
} from "./LocalisationMap"

const TABS: [ModalTab, string][] = [
  ["localisation", "Localisation"],
  ["annuaire", "Annuaire entreprise"],
]

/** Detail of a groupe in a modal: its localisation and the Annuaire Entreprises. */
export function GroupeModal({
  groupeId,
  tab,
  policy,
  actions,
  onTab,
  onClose,
}: {
  groupeId: number | null
  tab: ModalTab
  policy: Policy
  actions: GroupeActions
  onTab: (tab: ModalTab) => void
  onClose: () => void
}) {
  const detail = useGroupeDetail(groupeId)
  const groupe = detail.data
  return (
    <WaDialog
      open={groupeId !== null}
      label={groupe ? `Groupe #${groupe.id} · ${groupe.acteur.nom}` : "Groupe"}
      className="groupe-modal"
      lightDismiss
      onWaAfterHide={(event) => {
        // Ignore the events of nested elements (tooltips…)
        if (event.target === event.currentTarget) {
          onClose()
        }
      }}
    >
      {detail.error && <p className="error">{detail.error.message}</p>}
      {!groupe && !detail.error && <WaSpinner />}
      {groupe && (
        <>
          <div className="modal-meta">
            <StatutPill
              statut={groupe.statut}
              decision={{ par: groupe.decision_par, le: groupe.decision_le }}
            />
            <span className="mono faint">{groupe.acteur.identifiant_unique}</span>
            {groupe.is_new && policy.badge && (
              <span className="pill p-accent">{policy.badge}</span>
            )}
          </div>
          <WaTabGroup
            active={tab}
            onWaTabShow={(event) => onTab(event.detail.name as ModalTab)}
          >
            {TABS.map(([name, label]) => (
              <WaTab key={name} slot="nav" panel={name}>
                {label}
              </WaTab>
            ))}
            <WaTabPanel name="localisation">
              {tab === "localisation" && (
                <LocalisationTab groupe={groupe} actions={actions} />
              )}
            </WaTabPanel>
            <WaTabPanel name="annuaire">
              <AnnuaireTab groupe={groupe} />
            </WaTabPanel>
          </WaTabGroup>
        </>
      )}
    </WaDialog>
  )
}

const MODELE_OF_MARKER: Partial<Record<MarkerKey, Modele>> = {
  RevisionActeur: "RevisionActeur",
  ParentRevisionActeur: "ParentRevisionActeur",
}

const format = (point: { latitude: number; longitude: number }) =>
  `${point.latitude.toFixed(6)}, ${point.longitude.toFixed(6)}`

function LocalisationTab({
  groupe,
  actions,
}: {
  groupe: GroupeDetail
  actions: GroupeActions
}) {
  const { points, ligne: ligneKey, creer_correction } = groupe.localisation
  // The (latitude, longitude) ligne, possibly not existing yet
  const ligne = groupe.lignes.find((l) => l.key === ligneKey) ?? {
    key: `${groupe.id}:latitude,longitude`,
    champs: ["latitude", "longitude"],
  }
  const save = (modele: Modele, latitude: number, longitude: number) =>
    actions
      .upsertProposition(groupe, ligne, modele, {
        latitude: latitude.toFixed(6),
        longitude: longitude.toFixed(6),
      })
      .catch(() => {})

  // Localisation of the établissement in the Annuaire des entreprises
  const siret = groupe.annuaire.siret[0]
  const [showAnnuaire, setShowAnnuaire] = useState(false)
  const annuaire = useAnnuaireEntreprise("siret", siret?.valeur ?? "", showAnnuaire)
  const etablissement = annuaire.data?.etablissement
  const annuairePoint: MapPoint | null =
    showAnnuaire && etablissement?.latitude != null && etablissement.longitude != null
      ? {
          key: "AnnuaireEntreprises",
          latitude: etablissement.latitude,
          longitude: etablissement.longitude,
          draggable: false,
        }
      : null
  const mapPoints: MapPoint[] = annuairePoint ? [...points, annuairePoint] : points
  const byKey = Object.fromEntries(mapPoints.map((point) => [point.key, point]))
  // A new proposition starts from the current correction, else where the source,
  // the acteur or the Annuaire puts it
  const start = byKey.RevisionActeur ?? byKey.Acteur ?? byKey.Origin ?? annuairePoint
  // Marker shown above the others (click on it or on its legend)
  const [focused, setFocused] = useState<MarkerKey | null>(null)

  return (
    <div className="localisation">
      <LocalisationMap
        // A new map, framed on its points, for each groupe
        key={groupe.id}
        points={mapPoints}
        focused={focused}
        onFocus={setFocused}
        onMove={(key, latitude, longitude) => {
          const modele = MODELE_OF_MARKER[key]
          if (modele) {
            save(modele, latitude, longitude)
          }
        }}
      />
      <div className="legend-map">
        <h3>Légende</h3>
        {(Object.keys(MARKERS) as MarkerKey[])
          .filter((key) => key !== "AnnuaireEntreprises" || showAnnuaire)
          .map((key) => {
            const point = byKey[key]
            return (
              <div
                key={key}
                className={`legend-map__item${focused === key ? " legend-map__item--focused" : ""}`}
                role="button"
                tabIndex={0}
                aria-pressed={focused === key}
                title="Afficher ce marqueur au-dessus des autres"
                onClick={() => setFocused(key)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault()
                    setFocused(key)
                  }
                }}
              >
                <span
                  className="pin pin--legend"
                  style={{ "--pin-color": MARKERS[key].color } as React.CSSProperties}
                >
                  <span className="pin__head">
                    <span className="pin__text">{MARKERS[key].text}</span>
                  </span>
                </span>
                <div>
                  <div>{MARKERS[key].label}</div>
                  <div className="mono muted">
                    {point ? format(point) : "absent"}
                    {point?.draggable && <span className="hint"> · déplaçable</span>}
                  </div>
                  {key === "RevisionActeur" && creer_correction && (
                    <WaButton
                      size="small"
                      appearance="outlined"
                      disabled={!start}
                      title={
                        start
                          ? `Proposer la localisation ${format(start)} sur la correction, puis déplacer le marqueur`
                          : "Aucune position de départ"
                      }
                      onClick={(event) => {
                        event.stopPropagation()
                        if (start) {
                          setFocused("RevisionActeur")
                          save("RevisionActeur", start.latitude, start.longitude)
                        }
                      }}
                    >
                      Ajouter une correction de la localisation
                    </WaButton>
                  )}
                  {key === "AnnuaireEntreprises" && (
                    <AnnuaireLegend
                      siret={siret}
                      loading={annuaire.isFetching}
                      error={annuaire.error?.message}
                      adresse={etablissement?.adresse}
                      found={Boolean(annuaire.data?.etablissement)}
                      located={Boolean(annuairePoint)}
                    />
                  )}
                </div>
              </div>
            )
          })}
        {siret && !showAnnuaire && (
          <WaButton
            size="small"
            appearance="outlined"
            onClick={() => setShowAnnuaire(true)}
          >
            <WaIcon slot="start" name="map-pin" />
            Localisation Annuaire des entreprises
          </WaButton>
        )}
        <p className="hint">
          Relâcher un marqueur déplaçable enregistre aussitôt la position sur la ligne
          (latitude, longitude) de l’objet ; la ligne reste à valider.
        </p>
      </div>
    </div>
  )
}

function AnnuaireLegend({
  siret,
  loading,
  error,
  adresse,
  found,
  located,
}: {
  siret: Identifiant | undefined
  loading: boolean
  error: string | undefined
  adresse: string | undefined
  found: boolean
  located: boolean
}) {
  if (!siret) {
    return null
  }
  return (
    <div className="hint">
      SIRET {siret.valeur} ({siret.label.toLowerCase()}){loading && <WaSpinner />}
      {error && <div className="ae-ferme">{error}</div>}
      {!loading && !error && !found && (
        <div className="ae-ferme">établissement introuvable</div>
      )}
      {found && adresse && <div>{adresse}</div>}
      {found && !located && (
        <div className="ae-ferme">pas de localisation dans l’Annuaire</div>
      )}
    </div>
  )
}
