import pandas as pd
import pytest
from utils import logging_utils as log

from dags.sources.tasks.business_logic.keep_acteur_changed import keep_acteur_changed


@pytest.mark.parametrize(
    "df_acteur, df_acteur_from_db, df_acteur_expected, "
    "df_acteur_from_db_expected, metadata_expected",
    [
        # 1. EMPTY
        (
            pd.DataFrame(
                {
                    "nom": [],
                    "identifiant_unique": [],
                    "label_codes": [],
                    "source_code": [],
                    "identifiant_externe": [],
                    "acteur_type_code": [],
                    "acteur_service_codes": [],
                    "proposition_service_codes": [],
                }
            ),
            pd.DataFrame(
                {
                    "nom": [],
                    "identifiant_unique": [],
                    "label_codes": [],
                    "source_code": [],
                    "identifiant_externe": [],
                    "acteur_type_code": [],
                    "acteur_service_codes": [],
                    "proposition_service_codes": [],
                }
            ),
            pd.DataFrame(
                {
                    "nom": [],
                    "identifiant_unique": [],
                    "label_codes": [],
                    "source_code": [],
                    "identifiant_externe": [],
                    "acteur_type_code": [],
                    "acteur_service_codes": [],
                    "proposition_service_codes": [],
                }
            ),
            pd.DataFrame(
                {
                    "nom": [],
                    "identifiant_unique": [],
                    "label_codes": [],
                    "source_code": [],
                    "identifiant_externe": [],
                    "acteur_type_code": [],
                    "acteur_service_codes": [],
                    "proposition_service_codes": [],
                }
            ),
            {},
        ),
        # 2. SAME source / db - SAME list / dict order
        (
            pd.DataFrame(
                {
                    "nom": ["nom 1", "nom 2"],
                    "identifiant_unique": ["source1_id1", "source2_id2"],
                    "label_codes": [["label1", "label2"], ["label2", "label1"]],
                    "source_code": ["source1", "source2"],
                    "identifiant_externe": ["id1", "id2"],
                    "acteur_type_code": ["commerce", "ess"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                        ["service2", "service1"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            },
                            {
                                "action": "action2",
                                "sous_categories": ["souscat2", "souscat1"],
                            },
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1", "nom 2"],
                    "identifiant_unique": ["source1_id1", "source2_id2"],
                    "label_codes": [["label1", "label2"], ["label2", "label1"]],
                    "source_code": ["source1", "source2"],
                    "identifiant_externe": ["id1", "id2"],
                    "acteur_type_code": ["commerce", "ess"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                        ["service2", "service1"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            },
                            {
                                "action": "action2",
                                "sous_categories": ["souscat2", "souscat1"],
                            },
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": pd.Series([], dtype="object"),
                    "identifiant_unique": pd.Series([], dtype="object"),
                    "label_codes": pd.Series([], dtype="object"),
                    "source_code": pd.Series([], dtype="object"),
                    "identifiant_externe": pd.Series([], dtype="object"),
                    "acteur_type_code": pd.Series([], dtype="object"),
                    "acteur_service_codes": pd.Series([], dtype="object"),
                    "proposition_service_codes": pd.Series([], dtype="object"),
                }
            ),
            pd.DataFrame(
                {
                    "nom": pd.Series([], dtype="object"),
                    "identifiant_unique": pd.Series([], dtype="object"),
                    "label_codes": pd.Series([], dtype="object"),
                    "source_code": pd.Series([], dtype="object"),
                    "identifiant_externe": pd.Series([], dtype="object"),
                    "acteur_type_code": pd.Series([], dtype="object"),
                    "acteur_service_codes": pd.Series([], dtype="object"),
                    "proposition_service_codes": pd.Series([], dtype="object"),
                }
            ),
            {},
        ),
        # 3. SAME source / db - not ordered
        (
            pd.DataFrame(
                {
                    "nom": ["nom 1", "nom 2"],
                    "identifiant_unique": ["source1_id1", "source2_id2"],
                    "label_codes": [["label1", "label2"], ["label2", "label1"]],
                    "source_code": ["source1", "source2"],
                    "identifiant_externe": ["id1", "id2"],
                    "acteur_type_code": ["commerce", "ess"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                        ["service2", "service1"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            },
                            {
                                "action": "action2",
                                "sous_categories": ["souscat2", "souscat1"],
                            },
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1", "nom 2"],
                    "identifiant_unique": ["source1_id1", "source2_id2"],
                    "label_codes": [["label1", "label2"], ["label1", "label2"]],
                    "source_code": ["source1", "source2"],
                    "identifiant_externe": ["id1", "id2"],
                    "acteur_type_code": ["commerce", "ess"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat2", "souscat1"],
                            }
                        ],
                        [
                            {
                                "action": "action2",
                                "sous_categories": ["souscat2", "souscat1"],
                            },
                            {
                                "action": "action1",
                                "sous_categories": ["souscat2", "souscat1"],
                            },
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": pd.Series([], dtype="object"),
                    "identifiant_unique": pd.Series([], dtype="object"),
                    "label_codes": pd.Series([], dtype="object"),
                    "source_code": pd.Series([], dtype="object"),
                    "identifiant_externe": pd.Series([], dtype="object"),
                    "acteur_type_code": pd.Series([], dtype="object"),
                    "acteur_service_codes": pd.Series([], dtype="object"),
                    "proposition_service_codes": pd.Series([], dtype="object"),
                }
            ),
            pd.DataFrame(
                {
                    "nom": pd.Series([], dtype="object"),
                    "identifiant_unique": pd.Series([], dtype="object"),
                    "label_codes": pd.Series([], dtype="object"),
                    "source_code": pd.Series([], dtype="object"),
                    "identifiant_externe": pd.Series([], dtype="object"),
                    "acteur_type_code": pd.Series([], dtype="object"),
                    "acteur_service_codes": pd.Series([], dtype="object"),
                    "proposition_service_codes": pd.Series([], dtype="object"),
                }
            ),
            {},
        ),
        # 4. STR (nom) updated
        (
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 2"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 2"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            {
                "Nombre de mise à jour par champ": {
                    " ": ["MODIF", "SUP", "AJOUT"],
                    "nom": [1, 0, 0],
                }
            },
        ),
        # 5. LIST (acteur_service_codes) updated
        (
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service3"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service3"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            {
                "Nombre de mise à jour par champ": {
                    " ": ["MODIF", "SUP", "AJOUT"],
                    "acteur_service_codes": [1, 0, 0],
                }
            },
        ),
        # 6. LIST length (acteur_service_codes) updated
        (
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            {
                "Nombre de mise à jour par champ": {
                    " ": ["MODIF", "SUP", "AJOUT"],
                    "acteur_service_codes": [1, 0, 0],
                }
            },
        ),
        # 7. DICT (proposition_service_codes) updated
        (
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2", "souscat3"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2", "souscat3"],
                            }
                        ],
                    ],
                }
            ),
            {
                "Nombre de mise à jour par champ": {
                    " ": ["MODIF", "SUP", "AJOUT"],
                    "proposition_service_codes": [1, 0, 0],
                }
            },
        ),
        # 8. Keep from_db if not updated
        (
            pd.DataFrame(
                {
                    "nom": [],
                    "identifiant_unique": [],
                    "label_codes": [],
                    "source_code": [],
                    "identifiant_externe": [],
                    "acteur_type_code": [],
                    "acteur_service_codes": [],
                    "proposition_service_codes": [],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": [],
                    "identifiant_unique": [],
                    "label_codes": [],
                    "source_code": [],
                    "identifiant_externe": [],
                    "acteur_type_code": [],
                    "acteur_service_codes": [],
                    "proposition_service_codes": [],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            {},
        ),
        # 9. Keep from_source if not in db
        (
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": [],
                    "identifiant_unique": [],
                    "label_codes": [],
                    "source_code": [],
                    "identifiant_externe": [],
                    "acteur_type_code": [],
                    "acteur_service_codes": [],
                    "proposition_service_codes": [],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": [],
                    "identifiant_unique": [],
                    "label_codes": [],
                    "source_code": [],
                    "identifiant_externe": [],
                    "acteur_type_code": [],
                    "acteur_service_codes": [],
                    "proposition_service_codes": [],
                }
            ),
            {},
        ),
        # 10. FIELDS (nom, label_codes, proposition_service_codes) added
        (
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": [""],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [[]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [[]],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 1"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": [""],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [[]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [[]],
                }
            ),
            {
                "Nombre de mise à jour par champ": {
                    " ": ["MODIF", "SUP", "AJOUT"],
                    "label_codes": [0, 0, 1],
                    "nom": [0, 0, 1],
                    "proposition_service_codes": [0, 0, 1],
                }
            },
        ),
        # 11. FIELDS (nom, label_codes, proposition_service_codes) removed
        (
            pd.DataFrame(
                {
                    "nom": [""],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [[]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [[]],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 2"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            pd.DataFrame(
                {
                    "nom": [""],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [[]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [[]],
                }
            ),
            pd.DataFrame(
                {
                    "nom": ["nom 2"],
                    "identifiant_unique": ["source1_id1"],
                    "label_codes": [["label1", "label2"]],
                    "source_code": ["source1"],
                    "identifiant_externe": ["id1"],
                    "acteur_type_code": ["commerce"],
                    "acteur_service_codes": [
                        ["service1", "service2"],
                    ],
                    "proposition_service_codes": [
                        [
                            {
                                "action": "action1",
                                "sous_categories": ["souscat1", "souscat2"],
                            }
                        ],
                    ],
                }
            ),
            {
                "Nombre de mise à jour par champ": {
                    " ": ["MODIF", "SUP", "AJOUT"],
                    "label_codes": [0, 1, 0],
                    "nom": [0, 1, 0],
                    "proposition_service_codes": [0, 1, 0],
                }
            },
        ),
    ],
)
def test_keep_acteur_changed(
    df_acteur,
    df_acteur_from_db,
    df_acteur_expected,
    df_acteur_from_db_expected,
    metadata_expected,
    dag_config,
):
    df_acteur, df_acteur_from_db, metadata = keep_acteur_changed(
        df_normalized=df_acteur,
        df_acteur_from_db=df_acteur_from_db,
        dag_config=dag_config,
    )
    log.preview("df_acteur", df_acteur)
    log.preview("df_acteur_from_db", df_acteur_from_db)
    pd.testing.assert_frame_equal(df_acteur, df_acteur_expected)
    pd.testing.assert_frame_equal(df_acteur_from_db, df_acteur_from_db_expected)

    metadata = {k: sorted(v.items()) for k, v in metadata.items()}
    metadata_expected = {k: sorted(v.items()) for k, v in metadata_expected.items()}
    assert metadata == metadata_expected
