import pandas as pd
from fuzzywuzzy import fuzz
from sources.config import shared_constants as constants


def set_cohort_id(row):
    current_nom = row["nom"]
    current_adresse_ae = row["ae_adresse"]
    current_adresse_lvao = row["full_adresse"]
    current_naf = row["categorie_naf"]
    current_siret = row["siret"]
    current_siren = None
    current_siret_size = None
    if current_siret is not None:
        current_siret_size = len(current_siret.strip())
        current_siren = current_siret[:9]
    priorities = {
        "empty_siret": 12,
        "ownership_transferred_matching_category_lvao_address": 11,
        "ownership_transferred_matching_category_ae_address": 10,
        "ownership_transferred_different_category": 9,
        "ownership_transferred_different_names": 8,
        "relocation_same_siren_matching_name_and_naf": 7,
        "relocation_same_siren_matching_name_only": 6,
        "relocation_same_siren_not_matching_name": 5,
        "relocation": 4,
        "closed_0_open_candidates_address_result_included": 3,
        "closed_0_open_candidates": 2,
        "closed": 1,
    }

    best_outcome = "closed"
    highest_priority_level = 1
    best_candidate_index = -1
    total_nb_etablissements_ouverts = sum(
        candidate.get("nombre_etablissements_ouverts", 0)
        for candidate in row["ae_result"]
    )

    for index, candidate in enumerate(row["ae_result"]):
        nom_match_strength = fuzz.ratio(candidate["nom_candidat"], current_nom)
        adresse_lvao_match_ratio = fuzz.ratio(
            candidate["adresse_candidat"], current_adresse_lvao
        )
        adresse_ae_match_ratio = fuzz.ratio(
            candidate["adresse_candidat"], current_adresse_ae
        )
        candidate_siren = candidate["siret_candidat"][:9]
        if current_siret is None:
            best_outcome = "empty_siret"
            best_candidate_index = index
            break
        elif (
            adresse_lvao_match_ratio > 80
            and candidate["categorie_naf_candidat"] == current_naf
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
        ):
            best_outcome = "ownership_transferred_matching_category_lvao_address"
            best_candidate_index = index
            break
        elif (
            adresse_ae_match_ratio > 80
            and candidate["categorie_naf_candidat"] == current_naf
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
            and priorities["ownership_transferred_matching_category_ae_address"]
            > highest_priority_level
        ):
            best_outcome = "ownership_transferred_matching_category_ae_address"
            best_candidate_index = index
            break
        elif (
            (adresse_ae_match_ratio > 80 or adresse_lvao_match_ratio > 80)
            and candidate["categorie_naf_candidat"] != current_naf
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
            and priorities["ownership_transferred_different_category"]
            > highest_priority_level
        ):
            best_outcome = "ownership_transferred_different_category"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index
        elif (
            (adresse_ae_match_ratio > 80 or adresse_lvao_match_ratio > 80)
            and candidate["categorie_naf_candidat"] == current_naf
            and candidate["etat_admin_candidat"] == "A"
            and priorities["ownership_transferred_different_names"]
            > highest_priority_level
        ):
            best_outcome = "ownership_transferred_different_names"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index

        elif (
            candidate["nombre_etablissements_ouverts"] == 1
            and current_siren == candidate_siren
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
            and candidate["categorie_naf_candidat"] == current_naf
            and priorities["relocation_same_siren_matching_name_and_naf"]
            > highest_priority_level
        ):
            best_outcome = "relocation_same_siren_matching_name_and_naf"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index

        elif (
            candidate["nombre_etablissements_ouverts"] == 1
            and current_siren == candidate_siren
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
            and priorities["relocation_same_siren_matching_name_only"]
            > highest_priority_level
        ):
            best_outcome = "relocation_same_siren_matching_name_only"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index

        elif (
            candidate["nombre_etablissements_ouverts"] == 1
            and current_siren == candidate_siren
            and candidate["etat_admin_candidat"] == "A"
            and priorities["relocation_same_siren_not_matching_name"]
            > highest_priority_level
        ):
            best_outcome = "relocation_same_siren_not_matching_name"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index
        elif (
            candidate["adresse_candidat"] != current_adresse_ae
            and candidate["adresse_candidat"] != current_adresse_lvao
            and candidate["categorie_naf_candidat"] == current_naf
            and candidate["etat_admin_candidat"] == "A"
            and nom_match_strength > 80
            and priorities["relocation"] > highest_priority_level
        ):
            best_outcome = "relocation"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index

        elif (
            total_nb_etablissements_ouverts == 0
            and current_siret_size == 14
            and priorities["closed_0_open_candidates_address_result_included"]
            > highest_priority_level
        ):
            best_outcome = "closed_0_open_candidates_address_result_included"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index
        elif (
            candidate["nombre_etablissements_ouverts"] == 0
            and candidate["search_by_siret_candidat"]
            and current_siret_size == 14
            and priorities["closed_0_open_candidates"] > highest_priority_level
        ):
            best_outcome = "closed_0_open_candidates"
            highest_priority_level = priorities[best_outcome]
            best_candidate_index = index

    if best_candidate_index != -1:
        row["ae_result"][best_candidate_index]["used_for_decision"] = True

    return best_outcome


def combine_ae_result_dicts(row):
    ae_result_siret = (
        row["ae_result_siret"] if isinstance(row["ae_result_siret"], list) else []
    )
    ae_result_adresse = (
        row["ae_result_adresse"] if isinstance(row["ae_result_adresse"], list) else []
    )

    siret_tuples = [tuple(sorted(d.items())) for d in ae_result_siret]
    adresse_tuples = [tuple(sorted(d.items())) for d in ae_result_adresse]

    unique_dicts = set(siret_tuples + adresse_tuples)

    return [dict(t) for t in unique_dicts]


def update_statut(row):
    for result in row["ae_result"]:
        if (
            row["siret"] == result.get("siret_candidat")
            and result["search_by_siret_candidat"]
        ):
            if result["etat_admin_candidat"] == "A":
                return pd.Series(
                    [
                        constants.ACTEUR_ACTIF,
                        result["categorie_naf_candidat"],
                        result["adresse_candidat"],
                    ]
                )
            else:
                return pd.Series(
                    [
                        "SUPPRIME",
                        result["categorie_naf_candidat"],
                        result["adresse_candidat"],
                    ]
                )
    return pd.Series(["SUPPRIME", None, row["full_adresse"]])
