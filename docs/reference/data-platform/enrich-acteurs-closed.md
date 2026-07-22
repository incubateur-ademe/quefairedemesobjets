# Enrich — Acteurs fermés (`enrich_acteurs_closed`)

This DAG detects active acteurs whose SIRET is closed in the
[Annuaire Entreprises (AE)](https://annuaire-entreprises.data.gouv.fr/),
then either proposes a replacement SIRET or marks the acteur as inactive.
It first refreshes the dbt models
(`dbt build --select tag:marts,tag:enrich,tag:closed`), runs tests, then
generates suggestions for four mutually exclusive cohorts.

Each acteur yields one legacy `Suggestion` (1 suggestion per acteur, grouped
under a `SuggestionCohorte` per cohort).

> Source DAG: [`data-platform/dags/enrich/dags/enrich_acteurs_closed.py`](../../../data-platform/dags/enrich/dags/enrich_acteurs_closed.py)

---

## Shared pipeline — candidates and replacements

### Candidates

**dbt model:** `marts_enrich_acteurs_closed_candidates`

**Input population:**
active acteurs from `base_vueacteur` with a valid SIRET (14 numeric digits),
visible on the map or in opendata (`est_dans_carte` or `est_dans_opendata`),
joined with `int_ae_etablissement` where the establishment is closed
(`est_actif = FALSE`, i.e. `etat_administratif != 'A'` in AE).

The legal unit (`unite_est_actif`) is **not** filtered at this stage, so that
replacements within the same company can still be found even when the unit is
closed.

### Replacement search

**dbt model:** `marts_enrich_acteurs_closed_replaced`

For each candidate, active AE establishments (`est_actif = TRUE`) are matched
on **NAF**, **postal code**, **street number** and **normalized address**
(from the closed establishment's AE data).

When several matches exist, a single best replacement is kept
(`replacement_priority = 1`), prioritizing:

1. **Same SIREN** as the closed acteur's SIRET.
2. **Most words in common** between the acteur name and the replacement name
   (normalized strings).

Proposals with unavailable AE names are excluded.

---

## Cohort 1 — Replaced by a SIRET from the same SIREN

**dbt model:** `marts_enrich_acteurs_closed_suggest_replaced_same_siren`

**Input population:** acteurs from `marts_enrich_acteurs_closed_replaced` where
the proposed SIRET shares the same SIREN as the closed acteur.

**Proposal:** update the acteur's SIRET and SIREN to the replacement values,
set `siret_is_closed = False`, and record the replacement reason in
`parent_reason`.

---

## Cohort 2 — Replaced by a SIRET from a different SIREN

**dbt model:** `marts_enrich_acteurs_closed_suggest_replaced_other_siren`

**Input population:** acteurs from `marts_enrich_acteurs_closed_replaced` where
the proposed SIRET belongs to a **different** SIREN.

**Proposal:** same as cohort 1 (SIRET/SIREN update, `siret_is_closed = False`).

---

## Cohort 3 — Not replaced, legal unit closed

**dbt model:** `marts_enrich_acteurs_closed_suggest_not_replaced_unite`

**Input population:** candidates with a closed legal unit in AE
(`unite_est_actif = FALSE`) and **no** replacement found in
`marts_enrich_acteurs_closed_replaced`.

**Proposal:** set the acteur status to `INACTIF`, flag `siret_is_closed = True`,
with a reason indicating the SIRET is closed in AE and no replacement was
found.

---

## Cohort 4 — Not replaced, establishment closed only

**dbt model:** `marts_enrich_acteurs_closed_suggest_not_replaced_etablissement`

**Input population:** remaining candidates — establishment closed in AE but
legal unit still active (`unite_est_actif = TRUE`), excluded from cohorts 1–3
(no replacement found, not already classified as fully closed at unit level).

**Proposal:** same as cohort 3 (`INACTIF`, `siret_is_closed = True`).
