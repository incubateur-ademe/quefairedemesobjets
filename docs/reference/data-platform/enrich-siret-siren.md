# Enrich — Acteurs SIRET & SIREN (`enrich_siret_siren`)

This DAG fills in missing SIRET/SIREN identifiers for visible acteurs,
using the [Annuaire Entreprises (AE)](https://annuaire-entreprises.data.gouv.fr/).
It first refreshes the dbt models (`dbt run --select +tag:siren_siret`), then
generates grouped suggestions for two independent cohorts.

Suggestions use the `SuggestionGroupe` / `SuggestionUnitaire` mechanism
(non-legacy): one group per proposed value, one unitary suggestion per acteur.

> Source DAG: [`data-platform/dags/enrich/dags/enrich_siret_siren.py`](../../../data-platform/dags/enrich/dags/enrich_siret_siren.py)

---

## Cohort 1 — SIRET proposed from a known SIREN

**dbt model:** `marts_enrich_siret_from_siren`

**Input population** (`int_acteur_with_siren_without_siret`):
visible acteurs (`base_vueacteur_visible`) with a valid SIREN
(9 numeric digits) and an empty SIRET.

**Proposal rules** (cross-referenced with active AE establishments,
`base_ae_etablissement`, `etat_administratif = 'A'`):

1. **SIREN → unique SIRET**: if the SIREN has only one active establishment
   in AE (all postal codes combined), that SIRET is proposed.
2. **Otherwise, SIREN + postal code → unique SIRET**: if only one active
   establishment matches the acteur's SIREN + postal code pair, that SIRET is
   proposed.

An acteur is retained only if one of these two rules yields a non-null
proposal. Suggestions are grouped by proposed SIRET
(1 `SuggestionGroupe` per SIRET).

---

## Cohort 2 — SIREN proposed from a known SIRET

**dbt model:** `marts_enrich_siren_from_siret`

**Input population** (`int_acteur_with_siret_without_siren`):
visible acteurs with a valid SIRET (14 numeric digits) and an empty SIREN.

**Proposal rule**: join the acteur's SIRET with `base_ae_etablissement`; the
SIREN of the active AE establishment (`etat_administratif = 'A'`) is proposed.
Suggestions are grouped by proposed SIREN (1 `SuggestionGroupe` per SIREN).
