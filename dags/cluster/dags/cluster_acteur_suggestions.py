"""
DAG de suggestions de clusters pour les acteurs

Les suggestions sont écrites dans la table qfdmo_suggestions
Le traitement des suggestions est géré hors de ce DAG par
l'app django data_management
"""

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from airflow.utils.dates import days_ago
from cluster.config.constants import FIELDS_PARENT_DATA_EXCLUDED
from cluster.config.model import ClusterConfig
from cluster.tasks.airflow_logic.cluster_acteurs_clusters_display_task import (
    cluster_acteurs_clusters_display_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_clusters_validate_task import (
    cluster_acteurs_clusters_validate_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_config_create_task import (
    cluster_acteurs_config_create_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_normalize_task import (
    cluster_acteurs_normalize_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_parents_choose_data_task import (
    cluster_acteurs_parents_choose_data_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_parents_choose_new_task import (
    cluster_acteurs_parents_choose_new_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_read_task import (
    cluster_acteurs_read_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_suggestions_display_task import (
    cluster_acteurs_suggestions_display_task,
)
from cluster.tasks.airflow_logic.cluster_acteurs_suggestions_to_db_task import (
    cluster_acteurs_suggestions_to_db_task,
)
from cluster.ui import params_separators as UI_PARAMS_SEPARATORS
from utils.airflow_params import airflow_params_dropdown_from_mapping
from utils.django import django_model_fields_get, django_setup_full

# Setup Django avant import des modèles
django_setup_full()
from qfdmo.models import Acteur, ActeurType, Source  # noqa: E402

# -------------------------------------------
# Gestion des dropdowns des paramètres
# -------------------------------------------
# A noter que ce design pattern est a éviter au maximum
# car le code est executé au parsing des fichiers DAG
# selon min_file_process_interval
# https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html#config-scheduler-min-file-process-interval
# https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#top-level-python-code
# En revanche sans cette approche, il va falloir:
# - soit laisser le métier rentrer des paramètres complexes à la main
# - soit maintenir des mapping statiques ici
# Ces deux options semblent pires que l'inconvénient du top-level code
# sachant que le code executé demeure assez légé

# Récupération données DB
mapping_source_id_by_code = {obj.code: obj.id for obj in Source.objects.all()}
mapping_acteur_type_id_by_code = {obj.code: obj.id for obj in ActeurType.objects.all()}
# Création des dropdowns
dropdown_sources = airflow_params_dropdown_from_mapping(mapping_source_id_by_code)
dropdown_acteur_types = airflow_params_dropdown_from_mapping(
    mapping_acteur_type_id_by_code
)

fields_all = django_model_fields_get(Acteur)
fields_enrich = sorted(
    list(
        # We don't want to enrich calculated properties obviously
        # since these are computed
        set(django_model_fields_get(Acteur, include_properties=False))
        # And we exclude some fields based on business rules (ex: source)
        - set(FIELDS_PARENT_DATA_EXCLUDED)
    )
)
fields_enrich_excluded = list(set(fields_all) - set(fields_enrich))

# To display protected fields in UI without breaking it
# (Airflow UI doesn't wrap, it creates a long line which messes up inputs)
fields_enrich_excluded_ui = [
    fields_enrich_excluded[i : i + 5] for i in range(0, len(fields_enrich_excluded), 5)
]

DAG_ID = "cluster_acteur_suggestions"
PARAMS = {
    "dry_run": Param(
        True,
        type="boolean",
        description_md=f"""
            🚱 Si coché, aucune tâche d'écriture ne sera effectuée.
            Ceci permet de tester le DAG rapidement sans peur de
            casser quoi que ce soit (itérer plus vite)
            (ex: pas d'écriture des suggestions en DB,
            donc pas visible dans Django Admin).
            {UI_PARAMS_SEPARATORS.READ_ACTEURS}""",
    ),
    # TODO: permettre de ne sélectionner aucune source = toutes les sources
    "include_sources": Param(
        [],
        type=["null", "array"],
        # La terminologie Airflow n'est pas très heureuse
        # mais "examples" est bien la façon de faire des dropdowns
        # voir https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html
        examples=dropdown_sources,
        description_md="""**➕ INCLUSION ACTEURS**: seuls ceux qui proviennent
            de ces sources (opérateur **OU/OR**)

            💯 Si aucune valeur spécifiée =  tous les acteurs sont inclus
            """,
    ),
    "include_acteur_types": Param(
        [],
        type="array",
        examples=dropdown_acteur_types,
        description_md="""**➕ INCLUSION ACTEURS**: ceux qui sont de ces types
             (opérateur **OU/OR**)""",
    ),
    "include_only_if_regex_matches_nom": Param(
        "",
        type=["null", "string"],
        description_md="""**➕ INCLUSION ACTEURS**: ceux dont le champ 'nom'
            correspond à cette expression régulière ([voir recettes](https://www.notion.so/accelerateur-transition-ecologique-ademe/Expressions-r-guli-res-regex-1766523d57d780939a37edd60f367b75))

            🧹 Note: la normalisation basique est appliquée à la volée sur ce
            champ avant l'application de la regex pour simplifier les expressions

            0️⃣ Si aucune valeur spécifiée =  cette option n'a PAS d'effet""",
    ),
    "include_if_all_fields_filled": Param(
        ["code_postal"],
        type="array",
        examples=fields_all,
        description_md="""**➕ INCLUSION ACTEURS**: ceux dont tous ces champs
            sont **remplis** (opérateur **ET/AND**)

            exemple: travailler uniquement sur les acteurs avec SIRET
             """,
    ),
    "exclude_if_any_field_filled": Param(
        [],
        type=["null", "array"],
        examples=fields_all,
        description_md=f"""**🛑 EXCLUSION ACTEURS**: ceux dont n'importe quel
            de ces champs est **rempli** (opérateur **OU/OR**)

            exemple: travailler uniquement sur les acteurs SANS SIRET

            0️⃣ Si aucune valeur spécifiée =  cette option n'a PAS d'effet
            {UI_PARAMS_SEPARATORS.READ_PARENTS}
            """,
    ),
    "include_parents_only_if_regex_matches_nom": Param(
        "",
        type=["null", "string"],
        description_md=f"""**➕ INCLUSION PARENTS**: ceux dont le champ 'nom'
            correspond à cette expression régulière ([voir recettes](https://www.notion.so/accelerateur-transition-ecologique-ademe/Expressions-r-guli-res-regex-1766523d57d780939a37edd60f367b75))

            🧹 Note: la normalisation basique est appliquée à la volée sur ce
            champ avant l'application de la regex pour simplifier les expressions

            0️⃣ Si aucune valeur spécifiée =  cette option n'a PAS d'effet

            {UI_PARAMS_SEPARATORS.NORMALIZATION}""",
    ),
    "normalize_fields_basic": Param(
        [],
        type=["null", "array"],
        examples=fields_all,
        description_md=r"""Les champs à normaliser de manière basique:
             - minuscule
             - conversion des accents
             - suppression des caractères spéciaux et espaces superflus

            exemple: ' Château de l'île' -> 'chateau de l ile'

            💯 Si aucun champ spécifié =  s'applique à TOUS les champs

            💡 Les normalisations de cette option et des options suivantes
            sont appliquées dans l'ordre de la UI. Plusieurs normalisations
            peuvent être appliquées à un même champ à la suite.
            """,
    ),
    "normalize_fields_no_words_size1": Param(
        ["nom"],
        type=["null", "array"],
        examples=fields_all,
        description_md=r"""Les champs à normaliser en supprimant les mots
            de taille 1.

            exemple: 'Place à la montagne' -> 'Place la montagne'

            0️⃣ Si aucun champ spécifié = s'applique à AUCUN champ
            """,
    ),
    "normalize_fields_no_words_size2_or_less": Param(
        ["nom"],
        type=["null", "array"],
        examples=fields_all,
        description_md="""Les champs à normaliser en supprimant les mots
            de taille 2 ou moins.

            exemple: "Place à la montagne" -> "Place montagne"

            0️⃣ Si aucun champ spécifié = s'applique à AUCUN champ
            """,
    ),
    "normalize_fields_no_words_size3_or_less": Param(
        # Feedback métier: supprimer des mots de taille 3
        # commence à devenir radical, donc on laisse ce champ
        # vide par défaut
        [],
        type=["null", "array"],
        examples=fields_all,
        description_md=r"""Les champs à normaliser en supprimant les mots
            de taille 3 ou moins.

            exemple: 'rue de la montagne' -> 'montagne'

            0️⃣ Si aucun champ spécifié = s'applique à AUCUN champ
            """,
    ),
    "normalize_fields_order_unique_words": Param(
        [],
        type=["null", "array"],
        examples=fields_all,
        description_md=f"""Les champs à normaliser en ordonnant les mots
            par ordre alphabétique et en supprimant les doublons.

            exemple: 'rue de la montagne rue' -> 'de la montagne rue'

            💯 Si aucun champ spécifié =  s'applique à TOUS les champs

            {UI_PARAMS_SEPARATORS.CLUSTERING}
            """,
    ),
    "cluster_intra_source_is_allowed": Param(
        False,
        type="boolean",
        description_md="""**🔄 INTRA-SOURCE**: si coché, les acteurs d'une même
            source peuvent être clusterisés ensemble""",
    ),
    "cluster_fields_exact": Param(
        ["code_postal", "ville"],
        type="array",
        examples=fields_all,
        description_md=r"""Les champs sur lesquels on fait le groupage exact.
            exemple: ["code_postal", "ville"]""",
    ),
    "cluster_fields_fuzzy": Param(
        ["nom", "adresse"],
        type=["null", "array"],
        examples=fields_all,
        description_md=r"""Les champs sur lesquels on fait le groupage fuzzy.
            exemple: ["code_postal", "ville"]""",
    ),
    "cluster_fuzzy_threshold": Param(
        0.5,
        type="number",
        description_md=f"""Seuil de similarité pour le groupage fuzzy.
            0 = pas de similarité, 1 = similarité parfaite

            {UI_PARAMS_SEPARATORS.DEDUP_CHOOSE_PARENT}

            {UI_PARAMS_SEPARATORS.DEDUP_ENRICH_PARENT}""",
    ),
    "dedup_enrich_fields": Param(
        fields_enrich,
        type=["array"],
        examples=fields_enrich,
        description_md=f"""✍️ Champs à enrichir (certains champs de type calculés ou id
        sont exclus)

        Exclus:
        {'  \n'.join([', '.join(chunck) for chunck in fields_enrich_excluded_ui])}
        """,
    ),
    "dedup_enrich_exclude_sources": Param(
        [],
        type=["null", "array"],
        examples=dropdown_sources,
        description_md="""**❌ EXCLUSIONS SOURCES**: sources sur lequelles
            ne **JAMAIS** prendre de données""",
    ),
    "dedup_enrich_priority_sources": Param(
        [],
        type=["array"],
        examples=dropdown_sources,
        description_md=r"""**🔢 PRIORITES SOURCES**: sources sur lequelles
            on **PRÉFÈRE** prendre de données

            🔴 BUG UI AIRFLOW: ne sélectionner qu'une valeur car l'ordre
            n'est pas garanti 🔴
            voir https://github.com/apache/airflow/discussions/46475

            Ce n'est pas parce qu'une source est prioritaire qu'on va
            nécessairement en tirer de la donnée
            """,
    ),
    "dedup_enrich_keep_empty": Param(
        False,
        type="boolean",
        description_md=r"""**🗋 CONSERVER LE VIDE**: si OUI et qu'une valeur
        vide est rencontrée sur une source prioritaire, alors elle sera
        conservée""",
    ),
}
keys_missing_in_conf = list(set(PARAMS.keys()) - set(ClusterConfig.model_fields))
if keys_missing_in_conf:
    raise ValueError(f"Param Airflow {keys_missing_in_conf} non trouvé(s) en config")

with DAG(
    dag_id=DAG_ID,
    dag_display_name="Cluster - Acteurs - Suggestions",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        # Une date bidon dans le passée pour
        # par que Airflow "attende" que la date
        # soit atteinte
        "start_date": days_ago(1),
        # Notre donnée n'étant pas versionnée dans le temps,
        # faire du catchup n'a pas de sense
        "catchup": False,
        "email_on_failure": False,
        "email_on_retry": False,
        # Les tâches de ce DAG ne devrait pas avoir de problème
        # de perf donc 0 retries par défaut
        "retries": 0,
    },
    description=("Un DAG pour générer des suggestions de clustering pour les acteurs"),
    tags=["cluster", "acteurs", "suggestions"],
    params=PARAMS,
    schedule=None,
) as dag:
    chain(
        cluster_acteurs_config_create_task(dag=dag),
        cluster_acteurs_read_task(dag=dag),
        cluster_acteurs_normalize_task(dag=dag),
        cluster_acteurs_clusters_display_task(dag=dag),
        cluster_acteurs_clusters_validate_task(dag=dag),
        cluster_acteurs_parents_choose_new_task(dag=dag),
        cluster_acteurs_parents_choose_data_task(dag=dag),
        cluster_acteurs_suggestions_display_task(dag=dag),
        cluster_acteurs_suggestions_to_db_task(dag=dag),
    )
