import pandas as pd
import pytest
from utils.base_utils import extract_details


@pytest.mark.parametrize(
    "input_row, expected_output",
    [
        (
            {"adresse_format_ban": "123 Rue de Paris 75001 Paris"},
            pd.Series(["123 Rue de Paris", "75001", "Paris"]),
        ),
        (
            {"adresse_format_ban": "456 Avenue de Lyon 6900 Lyon"},
            pd.Series(["456 Avenue de Lyon", "06900", "Lyon"]),
        ),
        (
            {"adresse_format_ban": "789 Boulevard de Marseille 13001"},
            pd.Series(["789 Boulevard de Marseille", "13001", None]),
        ),
        ({"adresse_format_ban": None}, pd.Series([None, None, None])),
        ({"adresse_format_ban": "Rue de Lille"}, pd.Series([None, None, None])),
        ({"adresse_format_ban": "75001 Paris"}, pd.Series([None, "75001", "Paris"])),
        (
            {"adresse_format_ban": "Ancienne école Albert Camus 78190 TRAPPES"},
            pd.Series(["Ancienne école Albert Camus", "78190", "Trappes"]),
        ),
        (
            {
                "adresse_format_ban": (
                    "ZAC Liourat, Lot 10002, Avenue Denis Padovani 13127 VITROLLES"
                )
            },
            pd.Series(
                [
                    "ZAC Liourat, Lot 10002, Avenue Denis Padovani",
                    "13127",
                    "Vitrolles",
                ]
            ),
        ),
        (
            {
                "adresse_format_ban": (
                    "Centre commercial CAP 3000 - Unité C08 - Avenue Eugène Donadeï"
                    " 06700 SAINT LAURENT DU VAR"
                )
            },
            pd.Series(
                [
                    "Centre commercial CAP 3000 - Unité C08 - Avenue Eugène Donadeï",
                    "06700",
                    "Saint Laurent Du Var",
                ]
            ),
        ),
        (
            {"adresse_format_ban": "BP 70004 9201 SAINT-GIRONS CEDEX"},
            pd.Series(["BP 70004", "09201", "Saint-Girons"]),
        ),
        (
            {"adresse_format_ban": "KERNILIEN - PLOUISY BP 10227 22202 GUINGAMP CEDEX"},
            pd.Series(["KERNILIEN - PLOUISY BP 10227", "22202", "Guingamp"]),
        ),
        (
            {
                "adresse_format_ban": (
                    "ZAE PARC DES VARENNES 2 AVENUE DES 28 ARPENTS"
                    " 94862 BONNEUIL SUR MARNE Cedex"
                )
            },
            pd.Series(
                [
                    "ZAE PARC DES VARENNES 2 AVENUE DES 28 ARPENTS",
                    "94862",
                    "Bonneuil Sur Marne",
                ]
            ),
        ),
        (
            {
                "adresse_format_ban": (
                    "CC Beaulieu 6 rue du docteur Zamen CP 42 - Cellule MU6 - Niveau 1"
                    " 44272 NANTES CEDEX 2"
                )
            },
            pd.Series(
                [
                    "CC Beaulieu 6 rue du docteur Zamen CP 42 - Cellule MU6 - Niveau 1",
                    "44272",
                    "Nantes",
                ]
            ),
        ),
        (
            {
                "adresse_format_ban": (
                    "ZA Le Chatillon - CS 60247 71309 MONTCESU LES MINES CEDEX"
                )
            },
            pd.Series(["ZA Le Chatillon - CS 60247", "71309", "Montcesu Les Mines"]),
        ),
        (
            {"adresse_format_ban": 'RD 306, Lieudit "La Une" 77240 VERT SAINT DENIS'},
            pd.Series(['RD 306, Lieudit "La Une"', "77240", "Vert Saint Denis"]),
        ),
        # Lamballe*
        (
            {"adresse_format_ban": "Lanjouan 22400 LAMBALLE*"},
            pd.Series(["Lanjouan", "22400", "Lamballe"]),
        ),
    ],
)
def test_extract_details(input_row, expected_output):
    input_df = pd.DataFrame([input_row])
    result = extract_details(input_df.iloc[0])
    pd.testing.assert_series_equal(result, expected_output)
