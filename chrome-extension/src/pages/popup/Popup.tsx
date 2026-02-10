import React, { useEffect, useState } from "react"
import { Badge } from "@codegouvfr/react-dsfr/Badge"
import { Card } from "@codegouvfr/react-dsfr/Card"
import { Button } from "@codegouvfr/react-dsfr/Button"
import { Tag } from "@codegouvfr/react-dsfr/Tag"
import { Alert } from "@codegouvfr/react-dsfr/Alert"
import {
  DetectedIframe,
  PageAnalysis,
  SessionStorageData,
  MAIN_DOMAIN,
  CONVERSION_SCORE_KEYS,
} from "../../types"

const TYPE_LABELS: Record<string, string> = {
  carte: "Carte",
  carte_sur_mesure: "Carte sur mesure",
  carte_preconfiguree: "Carte preconfiguree",
  assistant: "Assistant",
  unknown: "Inconnu",
}

const TYPE_BADGE_SEVERITY: Record<
  string,
  "info" | "success" | "warning" | "error" | "new"
> = {
  carte: "info",
  carte_sur_mesure: "success",
  carte_preconfiguree: "new",
  assistant: "info",
  unknown: "warning",
}

function SessionStorageStatusBar({ data }: { data: SessionStorageData }) {
  const hasLocation = !!(data.adresse || data.latitude || data.longitude)

  const conversionEntries = CONVERSION_SCORE_KEYS.filter(
    (key) => data[key] !== null,
  ).map((key) => ({ key, value: data[key]! }))
  const conversionScore = conversionEntries.reduce(
    (sum, entry) => sum + parseInt(entry.value || "0", 10),
    0,
  )

  const CONVERSION_LABELS: Record<string, string> = {
    homePageView: "Page d'accueil",
    produitPageView: "Page produit",
    userInteractionWithMap: "Interaction carte",
    userInteractionWithSolutionDetails: "Details solution",
  }

  return (
    <div
      style={{
        borderTop: "1px solid var(--border-default-grey)",
        paddingTop: "0.75rem",
        marginTop: "0.75rem",
      }}
    >
      <h3 style={{ fontSize: "0.9rem", marginBottom: "0.5rem" }}>Session storage</h3>

      <div style={{ marginBottom: "0.5rem" }}>
        <strong style={{ fontSize: "0.75rem" }}>Localisation :</strong>{" "}
        {hasLocation ? (
          <Tag small iconId="fr-icon-map-pin-2-line">
            {data.adresse || `${data.latitude}, ${data.longitude}`}
          </Tag>
        ) : (
          <Tag small>Non renseignee</Tag>
        )}
      </div>

      <div style={{ marginBottom: "0.5rem" }}>
        <strong style={{ fontSize: "0.75rem" }}>Score de conversion :</strong>{" "}
        <Badge severity={conversionScore > 0 ? "success" : "info"} small noIcon>
          {conversionScore}
        </Badge>
        {conversionEntries.length > 0 && (
          <ul style={{ margin: "0.25rem 0", paddingLeft: "1rem" }}>
            {conversionEntries.map(({ key, value }) => (
              <li key={key} style={{ fontSize: "0.7rem" }}>
                {CONVERSION_LABELS[key] || key} : {value}
              </li>
            ))}
          </ul>
        )}
      </div>

      {data.qf_ifr && (
        <div style={{ marginBottom: "0.5rem" }}>
          <strong style={{ fontSize: "0.75rem" }}>Referrer iframe :</strong>{" "}
          <code style={{ fontSize: "0.65rem", wordBreak: "break-all" }}>
            {data.qf_ifr}
          </code>
        </div>
      )}
    </div>
  )
}

function IframeCard({ iframe }: { iframe: DetectedIframe }) {
  const adminUrl =
    iframe.type === "carte_sur_mesure" && iframe.slug
      ? `https://${MAIN_DOMAIN}/admin/qfdmo/carteconfig/?slug=${iframe.slug}`
      : null

  const iframeSrcUrl = iframe.src

  const dataAttrs = {
    ...iframe.scriptDataAttributes,
    ...iframe.iframeDataAttributes,
  }
  const hasDataAttrs = Object.keys(dataAttrs).length > 0

  const description = (
    <div>
      <div style={{ marginBottom: "0.5rem" }}>
        <Badge severity={TYPE_BADGE_SEVERITY[iframe.type]} small>
          {TYPE_LABELS[iframe.type]}
        </Badge>
        {iframe.slug && (
          <Badge severity="success" small noIcon style={{ marginLeft: "0.25rem" }}>
            {iframe.slug}
          </Badge>
        )}
      </div>

      <div style={{ fontSize: "0.75rem", marginBottom: "0.5rem" }}>
        <strong>Domaine :</strong> {iframe.domain}
      </div>

      {iframe.insideTemplate && (
        <div style={{ fontSize: "0.75rem", marginBottom: "0.5rem" }}>
          <Tag small iconId="fr-icon-eye-off-line">
            Dans un &lt;template&gt; (DOM virtuel)
          </Tag>
        </div>
      )}

      <div style={{ fontSize: "0.75rem", marginBottom: "0.5rem" }}>
        <strong>Inclusion :</strong>{" "}
        {iframe.hasAdjacentScript ? (
          <Tag small iconId="fr-icon-check-line">
            Via script
          </Tag>
        ) : (
          <Tag small iconId="fr-icon-warning-line">
            Iframe directe
          </Tag>
        )}
      </div>

      {iframe.scriptSrc && (
        <div style={{ fontSize: "0.75rem", marginBottom: "0.5rem" }}>
          <strong>Script :</strong>{" "}
          <code style={{ fontSize: "0.7rem", wordBreak: "break-all" }}>
            {iframe.scriptSrc.split("/").pop()}
          </code>
        </div>
      )}

      <div style={{ fontSize: "0.75rem", marginBottom: "0.5rem" }}>
        <strong>iframe-resizer :</strong>{" "}
        {iframe.hasIframeResizer ? (
          <Tag small iconId="fr-icon-check-line">
            Detecte
          </Tag>
        ) : (
          <Tag small iconId="fr-icon-close-line">
            Non detecte
          </Tag>
        )}
      </div>

      {hasDataAttrs && (
        <div style={{ fontSize: "0.75rem", marginBottom: "0.5rem" }}>
          <strong>Data-attributes :</strong>
          <ul style={{ margin: "0.25rem 0", paddingLeft: "1rem" }}>
            {Object.entries(dataAttrs).map(([key, value]) => (
              <li key={key} style={{ fontSize: "0.7rem", wordBreak: "break-all" }}>
                <code>{key}</code>=
                {value.length > 40 ? value.substring(0, 40) + "..." : value}
              </li>
            ))}
          </ul>
        </div>
      )}

      {iframe.warnings.length > 0 && (
        <div style={{ marginTop: "0.5rem" }}>
          {iframe.warnings.map((warning, idx) => (
            <Alert
              key={idx}
              severity={
                warning.severity === "error"
                  ? "error"
                  : warning.severity === "info"
                    ? "info"
                    : "warning"
              }
              description={warning.message}
              small
              style={{ marginBottom: "0.25rem" }}
            />
          ))}
        </div>
      )}
    </div>
  )

  const footer = (
    <ul className="fr-btns-group fr-btns-group--sm fr-btns-group--inline">
      <li>
        <Button
          size="small"
          priority="secondary"
          iconId="fr-icon-external-link-line"
          onClick={() => chrome.tabs.create({ url: iframeSrcUrl })}
        >
          Ouvrir l'iframe
        </Button>
      </li>
      {adminUrl && (
        <li>
          <Button
            size="small"
            priority="secondary"
            iconId="fr-icon-settings-5-line"
            onClick={() => chrome.tabs.create({ url: adminUrl })}
          >
            Admin carte
          </Button>
        </li>
      )}
    </ul>
  )

  return (
    <Card
      title={TYPE_LABELS[iframe.type]}
      titleAs="h3"
      desc={description}
      footer={footer}
      border
      size="small"
      style={{ marginBottom: "0.75rem" }}
    />
  )
}

export default function Popup() {
  const [analysis, setAnalysis] = useState<PageAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null

    async function fetchAnalysis() {
      try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
        if (!tab?.id) {
          setError("Aucun onglet actif trouve")
          setLoading(false)
          return
        }

        const response = await chrome.tabs.sendMessage(tab.id, { type: "ANALYZE_PAGE" })
        setAnalysis(response as PageAnalysis)
      } catch {
        setError(
          "Impossible d'analyser la page. Le content script n'est peut-etre pas charge.",
        )
      } finally {
        setLoading(false)
      }
    }

    fetchAnalysis()

    // Auto-refresh every 2s to pick up iframe-resizer once scripts finish loading
    intervalId = setInterval(fetchAnalysis, 2000)

    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [])

  return (
    <div
      style={{
        width: 420,
        padding: "1rem",
        fontFamily: "Marianne, system-ui, sans-serif",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", marginBottom: "1rem" }}>
        <h2 style={{ margin: 0, fontSize: "1.1rem" }}>
          Que faire de mes réutilisateurs ?
        </h2>
      </div>

      {loading && <p>Analyse en cours...</p>}

      {error && <Alert severity="error" description={error} small />}

      {analysis && analysis.iframes.length === 0 && (
        <Alert
          severity="info"
          description="Aucune iframe QFDMO detectee sur cette page."
          small
        />
      )}

      {analysis && analysis.iframes.length > 0 && (
        <>
          <div style={{ marginBottom: "0.75rem" }}>
            <Badge severity={analysis.totalWarnings > 0 ? "warning" : "success"} small>
              {analysis.iframes.length} iframe{analysis.iframes.length > 1 ? "s" : ""}{" "}
              detectee
              {analysis.iframes.length > 1 ? "s" : ""}
            </Badge>
            {analysis.totalWarnings > 0 && (
              <Badge severity="error" small style={{ marginLeft: "0.25rem" }}>
                {analysis.totalWarnings} avertissement
                {analysis.totalWarnings > 1 ? "s" : ""}
              </Badge>
            )}
          </div>

          {analysis.iframes.map((iframe, idx) => (
            <IframeCard key={idx} iframe={iframe} />
          ))}
        </>
      )}

      {analysis && analysis.isQfdmoPage && analysis.sessionStorage && (
        <SessionStorageStatusBar data={analysis.sessionStorage} />
      )}
    </div>
  )
}
