"""
DAG to suggest SIRET/SIREN enrichments for QFDMO acteurs:
- 1 cohorte to suggest a new SIRET for acteurs that have a known SIREN
- 1 cohorte to suggest a new SIREN for acteurs that have a known SIRET

Suggestions are grouped (1 SuggestionGroupe per proposed SIRET, resp. per SIRET
acteur) using
the non-legacy SuggestionGroupe/SuggestionUnitaire machinery, the same way
crawl_urls does with `use_legacy_suggestions=False`.
"""

from airflow import DAG
from enrich.config.cohorts import COHORTS
from enrich.config.dbt import DBT
from enrich.config.models import EnrichActeursSiretSirenConfig
from enrich.config.tasks import TASKS
from enrich.tasks.airflow_logic.enrich_dbt_models_refresh_task import (
    enrich_dbt_models_refresh_task,
)
from enrich.tasks.airflow_logic.enrich_siret_siren_suggest_task import (
    enrich_siret_siren_suggest_task,
)
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.models import config_to_airflow_params
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

with DAG(
    dag_id="enrich_siret_siren",
    dag_display_name="🏢 Enrichir - Acteurs SIRET & SIREN",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    description=(
        "Un DAG pour proposer un SIRET (depuis un SIREN connu) "
        "ou un SIREN (depuis un SIRET connu) pour les acteurs"
    ),
    doc_md="""
## 🏢 Enrichir - Acteurs SIRET & SIREN

Ce DAG complète les identifiants SIRET/SIREN manquants des acteurs visibles,
en s'appuyant sur l'Annuaire Entreprises (AE). Il rafraîchit d'abord les
modèles DBT (`dbt run --select +tag:siren_siret`), puis génère des suggestions
groupées pour deux cohortes indépendantes.

Les suggestions utilisent le mécanisme `SuggestionGroupe` / `SuggestionUnitaire`
(non legacy) : un groupe par valeur proposée, une suggestion unitaire par acteur.

---

### Cohorte 1 — 🏢 SIRET proposé depuis le SIREN connu

**Modèle DBT :** `marts_enrich_siret_from_siren`

**Population d'entrée** (`int_acteur_with_siren_without_siret`) :
acteurs visibles (`base_vueacteur_visible`) avec un SIREN valide
(9 chiffres numériques) et un SIRET vide.

**Règles de proposition** (croisement avec les établissements AE actifs,
`base_ae_etablissement`, `etat_administratif = 'A'`) :

1. **SIREN → SIRET unique** : si le SIREN ne possède qu'un seul établissement
   actif dans l'AE (tous codes postaux confondus), ce SIRET est proposé.
2. **Sinon, SIREN + code postal → SIRET unique** : si un seul établissement
   actif correspond au couple SIREN + code postal de l'acteur, ce SIRET est
   proposé.

Un acteur n'est retenu que si l'une de ces deux règles aboutit à une
proposition non nulle. Les suggestions sont regroupées par SIRET proposé
(1 `SuggestionGroupe` par SIRET).

---

### Cohorte 2 — 🏢 SIREN proposé depuis le SIRET connu

**Modèle DBT :** `marts_enrich_siren_from_siret`

**Population d'entrée** (`int_acteur_with_siret_without_siren`) :
acteurs visibles avec un SIRET valide (14 chiffres numériques) et un SIREN
vide.

**Règle de proposition** : jointure du SIRET de l'acteur avec
`base_ae_etablissement` ; le SIREN de l'établissement AE actif
(`etat_administratif = 'A'`) est proposé. Les suggestions sont regroupées
par SIREN proposé (1 `SuggestionGroupe` par SIREN).
""",
    tags=[
        TAGS.ENRICH,
        TAGS.SIREN,
        TAGS.SIRET,
        TAGS.ACTEURS,
        TAGS.SUGGESTIONS,
    ],
    schedule=None,
    start_date=START_DATES.DEFAULT,
    params=config_to_airflow_params(
        EnrichActeursSiretSirenConfig(
            dbt_models_refresh=True,
            dbt_models_refresh_command="dbt run --select +tag:siren_siret",
        )
    ),
) as dag:
    dbt_refresh = enrich_dbt_models_refresh_task(dag)

    # Cohorte 1: acteurs with a known SIREN -> suggest a new SIRET
    # 1 SuggestionGroupe per proposed SIRET
    suggest_siret_from_siren = enrich_siret_siren_suggest_task(
        dag,
        task_id=TASKS.ENRICH_SIRET_FROM_SIREN_SUGGESTIONS,
        cohort=COHORTS.SIRET_FROM_SIREN,
        dbt_model_name=DBT.MARTS_ENRICH_SIRET_FROM_SIREN,
        suggest_action="ENRICH_ACTEURS_SIRET",
        suggest_field="siret",
    )

    # Cohorte 2: acteurs with a known SIRET -> suggest a new SIREN
    # 1 SuggestionGroupe per SIRET
    suggest_siren_from_siret = enrich_siret_siren_suggest_task(
        dag,
        task_id=TASKS.ENRICH_SIREN_FROM_SIRET_SUGGESTIONS,
        cohort=COHORTS.SIREN_FROM_SIRET,
        dbt_model_name=DBT.MARTS_ENRICH_SIREN_FROM_SIRET,
        suggest_action="ENRICH_ACTEURS_SIREN",
        suggest_field="siren",
    )

    # Graph
    dbt_refresh >> suggest_siret_from_siren  # type: ignore
    dbt_refresh >> suggest_siren_from_siret  # type: ignore
