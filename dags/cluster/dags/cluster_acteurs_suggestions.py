"""
DAG de suggestions de clusters pour les acteurs

Les suggestions sont écrites dans la table qfdmo_suggestions
Le traitement des suggestions est géré hors de ce DAG par
l'app django data_management
"""

from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from cluster.tasks.airflow_logic import (
    cluster_acteurs_config_validate_task,
    cluster_acteurs_db_data_read_acteurs_task,
    cluster_acteurs_db_data_write_suggestions_task,
    cluster_acteurs_info_size1_task,
    cluster_acteurs_normalize_task,
    cluster_acteurs_suggestions_task,
)
from utils.airflow_params import airflow_params_dropdown_from_mapping
from utils.django import django_model_fields_attributes_get, django_setup_full

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

dropdown_acteur_columns = django_model_fields_attributes_get(Acteur)

UI_PARAMS_SEPARATOR_SELECTION = r"""

---

# Paramètres de sélection
Les paramètres suivants décident des acteurs à inclure
ou exclure comme candidats au clustering. Ce n'est pas
parce qu'un acteur est selectionné qu'il sera forcément clusterisé.
(ex: si il se retrouve tout seul sachant qu'on supprime
les clusters de taille 1)
"""

UI_PARAMS_SEPARATOR_NORMALIZATION = r"""

---

# Paramètres de normalisation
Les paramètres suivants définissent comment les valeurs
des champs vont être transformées avant le clustering.
"""

UI_PARAMS_SEPARATOR_CLUSTERING = r"""

---

# Paramètres de clustering
Les paramètres suivants définissent comment les acteurs
vont être regroupés en clusters.
"""


with DAG(
    dag_id="cluster_acteurs_suggestions",
    dag_display_name="Cluster - Acteurs - Suggestions",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        # Une date bidon dans le passée pour
        # par que Airflow "attende" que la date
        # soit atteinte
        "start_date": datetime(2025, 1, 1),
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
    params={
        "dry_run": Param(
            True,
            type="boolean",
            description_md=f"""🚱 Si coché, seules les tâches qui ne modifient pas
            la base de données seront exécutées.
            {UI_PARAMS_SEPARATOR_SELECTION}""",
        ),
        "include_source_codes": Param(
            [],
            type="array",
            # La terminologie Airflow n'est pas très heureuse
            # mais "examples" est bien la façon de faire des dropdowns
            # voir https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html
            examples=dropdown_sources,
            description_md="""**➕ INCLUSION ACTEURS**: seuls ceux qui proviennent
            de ces sources (opérateur **OU/OR**)""",
        ),
        "include_acteur_type_codes": Param(
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

            0️⃣ Si aucune valeur spécifiée =  cette option n'a PAS d'effet
            """,
        ),
        "include_if_all_fields_filled": Param(
            ["code_postal"],
            type="array",
            examples=dropdown_acteur_columns,
            description_md="""**➕ INCLUSION ACTEURS**: ceux dont tous ces champs
            sont **remplis** (opérateur **ET/AND**)

            exemple: travailler uniquement sur les acteurs avec SIRET
             """,
        ),
        "exclude_if_any_field_filled": Param(
            [],
            type=["null", "array"],
            examples=dropdown_acteur_columns,
            description_md=f"""**🛑 EXCLUSION ACTEURS**: ceux dont n'importe quel
            de ces champs est **rempli** (opérateur **OU/OR**)

            exemple: travailler uniquement sur les acteurs SANS SIRET

            0️⃣ Si aucune valeur spécifiée =  cette option n'a PAS d'effet
            {UI_PARAMS_SEPARATOR_NORMALIZATION}
            """,
        ),
        "normalize_fields_basic": Param(
            [],
            type=["null", "array"],
            examples=dropdown_acteur_columns,
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
            examples=dropdown_acteur_columns,
            description_md=r"""Les champs à normaliser en supprimant les mots
            de taille 1.

            exemple: 'Place à la montagne' -> 'Place la montagne'

            0️⃣ Si aucun champ spécifié = s'applique à AUCUN champ
            """,
        ),
        "normalize_fields_no_words_size2_or_less": Param(
            ["nom"],
            type=["null", "array"],
            examples=dropdown_acteur_columns,
            description_md="""Les champs à normaliser en supprimant les mots
            de taille 2 ou moins.

            exemple: "Place à la montagne" -> "Place montagne"

            0️⃣ Si aucun champ spécifié = s'applique à AUCUN champ
            """,
        ),
        "normalize_fields_no_words_size3_or_less": Param(
            ["nom"],
            type=["null", "array"],
            examples=dropdown_acteur_columns,
            description_md=r"""Les champs à normaliser en supprimant les mots
            de taille 3 ou moins.

            exemple: 'rue de la montagne' -> 'montagne'

            0️⃣ Si aucun champ spécifié = s'applique à AUCUN champ
            """,
        ),
        "normalize_fields_order_unique_words": Param(
            [],
            type=["null", "array"],
            examples=dropdown_acteur_columns,
            description_md=f"""Les champs à normaliser en ordonnant les mots
            par ordre alphabétique et en supprimant les doublons.

            exemple: 'rue de la montagne rue' -> 'de la montagne rue'

            💯 Si aucun champ spécifié =  s'applique à TOUS les champs

            {UI_PARAMS_SEPARATOR_CLUSTERING}
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
            examples=dropdown_acteur_columns,
            description_md=r"""Les champs sur lesquels on fait le groupage exact.
            exemple: ["code_postal", "ville"]""",
        ),
        "cluster_fields_fuzzy": Param(
            ["nom", "adresse"],
            type="array",
            examples=dropdown_acteur_columns,
            description_md=r"""Les champs sur lesquels on fait le groupage fuzzy.
            exemple: ["code_postal", "ville"]""",
        ),
        "cluster_fuzzy_threshold": Param(
            0.5,
            type="number",
            description_md="""Seuil de similarité pour le groupage fuzzy.
            0 = pas de similarité, 1 = similarité parfaite""",
        ),
    },
    schedule=None,
) as dag:
    chain(
        cluster_acteurs_config_validate_task(dag=dag),
        cluster_acteurs_db_data_read_acteurs_task(dag=dag),
        cluster_acteurs_normalize_task(dag=dag),
        cluster_acteurs_info_size1_task(dag=dag),
        cluster_acteurs_suggestions_task(dag=dag),
        cluster_acteurs_db_data_write_suggestions_task(dag=dag),
    )
