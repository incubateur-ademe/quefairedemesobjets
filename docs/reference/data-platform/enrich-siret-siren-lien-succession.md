# Enrich — Acteurs SIRET & SIREN (lien succession) (`enrich_siret_siren_lien_succession`)

This DAG proposes SIREN/SIRET successor replacements for visible acteurs,
using resolved [Annuaire Entreprises (AE)](https://annuaire-entreprises.data.gouv.fr/)
succession links. It first refreshes the dbt models
(`dbt run --select +tag:lien_succession`), runs tests, then generates grouped
suggestions for one cohort.

Suggestions use the `SuggestionGroupe` / `SuggestionUnitaire` mechanism
(non-legacy): one group per `(source SIREN, source SIRET) -> (target SIREN,
target SIRET)` mapping, one unitary suggestion per acteur.

> Source DAG: [`data-platform/dags/enrich/dags/enrich_siret_siren_lien_succession.py`](../../../data-platform/dags/enrich/dags/enrich_siret_siren_lien_succession.py)

---

## Cohort — SIREN/SIRET successor from lien succession

**dbt model:** `exposure_stats_acteur_siret_successeur`

**Input population:** visible acteurs from `marts_ae_lien_succession_resolved_vueacteur`
with an active AE successor establishment. Acteurs whose current SIREN/SIRET
couple already matches the successor couple are excluded at suggestion time.

**Proposal:** update both `siren` and `siret` to the resolved successor values.

**Grouping rules:**

- Acteurs sharing the same source couple and the same proposed successor couple
  are grouped in a single `SuggestionGroupe`.
- Acteurs with different source couples are split into different groups, even
  when the proposed successor couple is identical.
