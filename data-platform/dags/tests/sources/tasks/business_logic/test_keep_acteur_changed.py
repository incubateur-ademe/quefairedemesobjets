import numpy as np
import pandas as pd
import pytest
from utils import logging_utils as log

from dags.sources.tasks.business_logic.keep_acteur_changed import (
    ActeurComparator,
    ColumnDiff,
    keep_acteur_changed,
)


class TestKeepActeurChanged:
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
                        "statut": [],
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
                        "statut": [],
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
                        "statut": [],
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
                        "statut": [],
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
                        "statut": ["actif", "actif"],
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
                        "statut": ["actif", "actif"],
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
                        "statut": pd.Series([], dtype="object"),
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
                        "statut": pd.Series([], dtype="object"),
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
                        "statut": ["actif", "actif"],
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
                        "statut": ["actif", "actif"],
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
                        "statut": pd.Series([], dtype="object"),
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
                        "statut": pd.Series([], dtype="object"),
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
                    }
                ),
                {
                    "Nombre de mises à jour par champ": {
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
                    }
                ),
                {
                    "Nombre de mises à jour par champ": {
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
                    }
                ),
                {
                    "Nombre de mises à jour par champ": {
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
                        "statut": ["actif"],
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
                                    "sous_categories": [
                                        "souscat1",
                                        "souscat2",
                                        "souscat3",
                                    ],
                                }
                            ],
                        ],
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                                    "sous_categories": [
                                        "souscat1",
                                        "souscat2",
                                        "souscat3",
                                    ],
                                }
                            ],
                        ],
                        "statut": ["actif"],
                    }
                ),
                {
                    "Nombre de mises à jour par champ": {
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
                        "statut": [],
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
                        "statut": ["actif"],
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
                        "statut": [],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": [],
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
                        "statut": ["actif"],
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
                        "statut": [],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
                    }
                ),
                {
                    "Nombre de mises à jour par champ": {
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
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
                        "statut": ["actif"],
                    }
                ),
                {
                    "Nombre de mises à jour par champ": {
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
        self,
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

        metadata = {
            k: sorted(v.items()) if isinstance(v, dict) else v
            for k, v in metadata.items()
        }
        metadata_expected = {
            k: sorted(v.items()) if isinstance(v, dict) else v
            for k, v in metadata_expected.items()
        }
        assert metadata == metadata_expected

    def test_keep_acteur_changed_same_acteur_but_different_identifiant_unique(
        self, dag_config
    ):
        df_normalized = pd.DataFrame(
            {
                "nom": ["nom 1"],
                "identifiant_unique": ["source1_id1"],
                "source_code": ["source1"],
                "identifiant_externe": ["id1"],
                "label_codes": [[]],
                "acteur_type_code": [[]],
                "acteur_service_codes": [[]],
                "proposition_service_codes": [[]],
                "statut": ["actif"],
            }
        )
        df_acteur_from_db = pd.DataFrame(
            {
                "nom": ["nom 1"],
                "identifiant_unique": ["source1_id_old"],
                "source_code": ["source1"],
                "identifiant_externe": ["id1"],
                "label_codes": [[]],
                "acteur_type_code": [[]],
                "acteur_service_codes": [[]],
                "proposition_service_codes": [[]],
                "statut": ["actif"],
            }
        )
        df_expected = pd.DataFrame(
            {
                "nom": [],
                "identifiant_unique": [],
                "source_code": [],
                "identifiant_externe": [],
                "label_codes": [],
                "acteur_type_code": [],
                "acteur_service_codes": [],
                "proposition_service_codes": [],
                "statut": [],
            }
        )

        df_acteur, df_acteur_from_db, metadata = keep_acteur_changed(
            df_normalized=df_normalized,
            df_acteur_from_db=df_acteur_from_db,
            dag_config=dag_config,
        )

        pd.testing.assert_frame_equal(df_acteur, df_expected, check_dtype=False)
        pd.testing.assert_frame_equal(df_acteur_from_db, df_expected, check_dtype=False)
        assert metadata == {}

    def test_keep_acteur_changed_same_acteur_but_different_identifiant_unique2(
        self, dag_config
    ):
        df_normalized = pd.DataFrame(
            {
                "nom": ["nom 1", "nom 2"],
                "identifiant_unique": ["source1_id1", "source1_id2"],
                "source_code": ["source1", "source1"],
                "identifiant_externe": ["id1", "id2"],
                "label_codes": [[], []],
                "acteur_type_code": [[], []],
                "acteur_service_codes": [[], []],
                "proposition_service_codes": [[], []],
                "statut": ["actif", "actif"],
            }
        )
        df_acteur_from_db = pd.DataFrame(
            {
                "nom": ["nom 1", "nom 3"],
                "identifiant_unique": ["source1_id_old", "source1_id3"],
                "source_code": ["source1", "source1"],
                "identifiant_externe": ["id1", "id3"],
                "label_codes": [[], []],
                "acteur_type_code": [[], []],
                "acteur_service_codes": [[], []],
                "proposition_service_codes": [[], []],
                "statut": ["actif", "actif"],
            }
        )
        df_expected = pd.DataFrame(
            {
                "nom": ["nom 2"],
                "identifiant_unique": ["source1_id2"],
                "source_code": ["source1"],
                "identifiant_externe": ["id2"],
                "label_codes": [[]],
                "acteur_type_code": [[]],
                "acteur_service_codes": [[]],
                "proposition_service_codes": [[]],
                "statut": ["actif"],
            }
        )
        df_expected_from_db = pd.DataFrame(
            {
                "nom": ["nom 3"],
                "identifiant_unique": ["source1_id3"],
                "source_code": ["source1"],
                "identifiant_externe": ["id3"],
                "label_codes": [[]],
                "acteur_type_code": [[]],
                "acteur_service_codes": [[]],
                "proposition_service_codes": [[]],
                "statut": ["actif"],
            }
        )

        df_acteur, df_acteur_from_db, metadata = keep_acteur_changed(
            df_normalized=df_normalized,
            df_acteur_from_db=df_acteur_from_db,
            dag_config=dag_config,
        )

        pd.testing.assert_frame_equal(
            df_acteur.reset_index(drop=True),
            df_expected.reset_index(drop=True),
            check_dtype=False,
        )
        pd.testing.assert_frame_equal(
            df_acteur_from_db.reset_index(drop=True),
            df_expected_from_db.reset_index(drop=True),
            check_dtype=False,
        )
        assert metadata == {}


def test_keep_acteur_changed_ignores_anonymized_acteurs(dag_config):
    """Test that anonymized actors for GDPR are ignored in both datasets"""
    df_normalized = pd.DataFrame(
        {
            "nom": ["nom 1", "nom 2", "nom 3 modifié"],
            "identifiant_unique": ["source1_id1", "source1_id2", "source1_id3"],
            "source_code": ["source1", "source1", "source1"],
            "identifiant_externe": ["id1", "id2", "id3"],
            "label_codes": [["label1"], ["label2"], ["label3"]],
            "acteur_type_code": ["commerce", "ess", "commerce"],
            "acteur_service_codes": [["service1"], ["service2"], ["service3"]],
            "proposition_service_codes": [
                [{"action": "action1", "sous_categories": ["souscat1"]}],
                [{"action": "action2", "sous_categories": ["souscat2"]}],
                [{"action": "action3", "sous_categories": ["souscat3"]}],
            ],
            "statut": ["actif", "actif", "actif"],
        }
    )
    df_acteur_from_db = pd.DataFrame(
        {
            "nom": ["nom 1", "ANONYMISE POUR RAISON RGPD", "nom 3"],
            "identifiant_unique": ["source1_id1", "source1_id2", "source1_id3"],
            "source_code": ["source1", "source1", "source1"],
            "identifiant_externe": ["id1", "id2", "id3"],
            "label_codes": [["label1"], ["label2"], ["label3"]],
            "acteur_type_code": ["commerce", "ess", "commerce"],
            "acteur_service_codes": [["service1"], ["service2"], ["service3"]],
            "proposition_service_codes": [
                [{"action": "action1", "sous_categories": ["souscat1"]}],
                [{"action": "action2", "sous_categories": ["souscat2"]}],
                [{"action": "action3", "sous_categories": ["souscat3"]}],
            ],
            "statut": ["actif", "actif", "actif"],
        }
    )

    # Expected result:
    # - source1_id1 doesn't change, so filtered out
    # - source1_id2 is anonymized, so filtered out
    # - source1_id3 changes, so kept
    df_normalized_expected = pd.DataFrame(
        {
            "nom": ["nom 3 modifié"],
            "identifiant_unique": ["source1_id3"],
            "source_code": ["source1"],
            "identifiant_externe": ["id3"],
            "label_codes": [["label3"]],
            "acteur_type_code": ["commerce"],
            "acteur_service_codes": [["service3"]],
            "proposition_service_codes": [
                [{"action": "action3", "sous_categories": ["souscat3"]}]
            ],
            "statut": ["actif"],
        }
    )
    df_acteur_from_db_expected = pd.DataFrame(
        {
            "nom": ["nom 3"],
            "identifiant_unique": ["source1_id3"],
            "source_code": ["source1"],
            "identifiant_externe": ["id3"],
            "label_codes": [["label3"]],
            "acteur_type_code": ["commerce"],
            "acteur_service_codes": [["service3"]],
            "proposition_service_codes": [
                [{"action": "action3", "sous_categories": ["souscat3"]}]
            ],
            "statut": ["actif"],
        }
    )

    df_normalized_result, df_acteur_from_db_result, metadata = keep_acteur_changed(
        df_normalized=df_normalized,
        df_acteur_from_db=df_acteur_from_db,
        dag_config=dag_config,
    )

    # Verify that other actors are processed correctly
    pd.testing.assert_frame_equal(
        df_normalized_result.reset_index(drop=True),
        df_normalized_expected.reset_index(drop=True),
        check_dtype=False,
    )
    pd.testing.assert_frame_equal(
        df_acteur_from_db_result.reset_index(drop=True),
        df_acteur_from_db_expected.reset_index(drop=True),
        check_dtype=False,
    )

    # Verify metadata about ignored anonymized actors
    assert "Nombre d'acteurs mis à jour ignorés car anonymisés pour RGPD" in metadata
    assert metadata["Nombre d'acteurs mis à jour ignorés car anonymisés pour RGPD"] == 1

    # Verify metadata about modifications
    assert "Nombre de mises à jour par champ" in metadata
    assert metadata["Nombre de mises à jour par champ"]["nom"] == [
        1,
        0,
        0,
    ]  # 1 modification


class TestColumnDiff:

    def test_init_default_values(self):
        """Test the default initialization of ColumnDiff"""
        diff = ColumnDiff()
        assert diff.modif == 0
        assert diff.sup == 0
        assert diff.ajout == 0

    @pytest.mark.parametrize(
        "changes,expected_modif,expected_sup,expected_ajout",
        [
            ([1, 0, 0], 1, 0, 0),  # modification
            ([0, 1, 0], 0, 1, 0),  # deletion
            ([0, 0, 1], 0, 0, 1),  # addition
        ],
        ids=["modif", "sup", "ajout"],
    )
    def test_add_single_change(
        self, changes, expected_modif, expected_sup, expected_ajout
    ):
        """Test adding a single change"""
        diff = ColumnDiff()
        diff.add(changes)
        assert diff.modif == expected_modif
        assert diff.sup == expected_sup
        assert diff.ajout == expected_ajout

    def test_add_multiple(self):
        """Test adding multiple changes"""
        diff = ColumnDiff()
        diff.add([1, 0, 0])
        diff.add([0, 1, 0])
        diff.add([0, 0, 1])
        assert diff.modif == 1
        assert diff.sup == 1
        assert diff.ajout == 1


class TestActeurComparator:
    """Tests for the ActeurComparator class"""

    def test_init(self):
        """Test the initialization of ActeurComparator"""
        columns = {"col1", "col2", "identifiant_unique"}
        comparator = ActeurComparator(columns)

        # identifiant_unique should be removed
        assert "identifiant_unique" not in comparator.columns_to_compare
        assert "col1" in comparator.columns_to_compare
        assert "col2" in comparator.columns_to_compare
        assert comparator.metadata == {}

    @pytest.mark.parametrize(
        "list1,list2,expected",
        [
            ([1, 2, 3], [1, 2, 3], False),  # same order
            ([1, 2, 3], [3, 1, 2], False),  # different order, identical content
            ([1, 2, 3], [1, 2, 4], True),  # different content
            ([1, 2, 3], [1, 2], True),  # different length
        ],
        ids=["same_order", "different_order", "different_content", "different_length"],
    )
    def test_list_field_changed(self, list1, list2, expected):
        """Test list comparison"""
        comparator = ActeurComparator({"field1"})
        assert comparator._list_field_changed(list1, list2) == expected

    @pytest.mark.parametrize(
        "pad1,pad2,expected",
        [
            (  # identical
                [
                    {"type": "departement", "valeur": "75"},
                    {"type": "region", "valeur": "11"},
                ],
                [
                    {"type": "departement", "valeur": "75"},
                    {"type": "region", "valeur": "11"},
                ],
                False,
            ),
            (  # different order
                [
                    {"type": "region", "valeur": "11"},
                    {"type": "departement", "valeur": "75"},
                ],
                [
                    {"type": "departement", "valeur": "75"},
                    {"type": "region", "valeur": "11"},
                ],
                False,
            ),
            (  # different values
                [
                    {"type": "departement", "valeur": "75"},
                    {"type": "region", "valeur": "11"},
                ],
                [
                    {"type": "departement", "valeur": "75"},
                    {"type": "region", "valeur": "12"},
                ],
                True,
            ),
        ],
        ids=["identical", "different_order", "different_values"],
    )
    def test_perimetre_adomiciles_changed(self, pad1, pad2, expected):
        """Test comparison of home service perimeters"""
        comparator = ActeurComparator({"field1"})
        assert comparator._perimetre_adomiciles_changed(pad1, pad2) == expected

    @pytest.mark.parametrize(
        "ps1,ps2,expected",
        [
            (  # identical (sous_categories in different order)
                [
                    {"action": "reparer", "sous_categories": ["velo", "ordinateur"]},
                    {"action": "donner", "sous_categories": ["vetement"]},
                ],
                [
                    {"action": "reparer", "sous_categories": ["ordinateur", "velo"]},
                    {"action": "donner", "sous_categories": ["vetement"]},
                ],
                False,
            ),
            (  # different order of actions
                [
                    {"action": "donner", "sous_categories": ["vetement"]},
                    {"action": "reparer", "sous_categories": ["velo", "ordinateur"]},
                ],
                [
                    {"action": "reparer", "sous_categories": ["ordinateur", "velo"]},
                    {"action": "donner", "sous_categories": ["vetement"]},
                ],
                False,
            ),
            (  # different values
                [
                    {"action": "reparer", "sous_categories": ["velo"]},
                    {"action": "donner", "sous_categories": ["vetement"]},
                ],
                [
                    {"action": "reparer", "sous_categories": ["ordinateur"]},
                    {"action": "donner", "sous_categories": ["vetement"]},
                ],
                True,
            ),
        ],
        ids=["identical", "different_order", "different_values"],
    )
    def test_proposition_services_changed(self, ps1, ps2, expected):
        """Test comparison of service propositions"""
        comparator = ActeurComparator({"field1"})
        assert comparator._proposition_services_changed(ps1, ps2) == expected

    @pytest.mark.parametrize(
        "value_source,value_db,expected",
        [
            ("value1", "value2", [1, 0, 0]),  # modification
            ("", "value", [0, 1, 0]),  # deletion with empty string
            (None, "value", [0, 1, 0]),  # deletion with None
            ("value", "", [0, 0, 1]),  # addition with empty string
            ("value", None, [0, 0, 1]),  # addition with None
        ],
        ids=["modif", "sup_empty", "sup_none", "ajout_empty", "ajout_none"],
    )
    def test_get_diff_type(self, value_source, value_db, expected):
        """Test determining the type of difference"""
        comparator = ActeurComparator({"field1"})
        diff_type = comparator._get_diff_type(value_source, value_db)
        assert diff_type == expected

    def test_field_changed_simple_string_no_change(self):
        """Test field_changed with identical strings"""
        comparator = ActeurComparator({"nom", "email"})
        row_source = {"nom": "Acteur 1", "email": "test@example.com"}
        row_db = {"nom": "Acteur 1", "email": "test@example.com"}

        result = comparator.field_changed(row_source, row_db)
        assert result == {}
        assert comparator.metadata == {}

    def test_field_changed_simple_string_changed(self):
        """Test field_changed with different strings"""
        comparator = ActeurComparator({"nom", "email"})
        row_source = {"nom": "Acteur 1 modifié", "email": "test@example.com"}
        row_db = {"nom": "Acteur 1", "email": "test@example.com"}

        result = comparator.field_changed(row_source, row_db)
        assert "nom" in result
        assert result["nom"] == [1, 0, 0]  # MODIF (modification)
        assert "email" not in result
        assert "nom" in comparator.metadata
        assert comparator.metadata["nom"].modif == 1

    @pytest.mark.parametrize(
        "row_source,row_db,expected_has_change",
        [
            (  # different lists
                {"labels": [1, 2, 3]},
                {"labels": [1, 2, 4]},
                True,
            ),
            (  # identical lists, different order
                {"labels": [3, 1, 2]},
                {"labels": [1, 2, 3]},
                False,
            ),
        ],
        ids=["different_values", "same_different_order"],
    )
    def test_field_changed_list_values(self, row_source, row_db, expected_has_change):
        """Test field_changed with lists"""
        comparator = ActeurComparator({"labels"})
        result = comparator.field_changed(row_source, row_db)

        if expected_has_change:
            assert "labels" in result
            assert result["labels"] == [1, 0, 0]  # MODIF (modification)
        else:
            assert result == {}

    def test_field_changed_proposition_service_codes(self):
        """Test field_changed with proposition_service_codes"""
        comparator = ActeurComparator({"proposition_service_codes"})
        row_source = {
            "proposition_service_codes": [
                {"action": "reparer", "sous_categories": ["velo"]},
            ]
        }
        row_db = {
            "proposition_service_codes": [
                {"action": "reparer", "sous_categories": ["ordinateur"]},
            ]
        }

        result = comparator.field_changed(row_source, row_db)
        assert "proposition_service_codes" in result

    def test_field_changed_perimetre_adomicile_codes(self):
        """Test field_changed with perimetre_adomicile_codes"""
        comparator = ActeurComparator({"perimetre_adomicile_codes"})
        row_source = {
            "perimetre_adomicile_codes": [
                {"type": "departement", "valeur": "75"},
            ]
        }
        row_db = {
            "perimetre_adomicile_codes": [
                {"type": "departement", "valeur": "78"},
            ]
        }

        result = comparator.field_changed(row_source, row_db)
        assert "perimetre_adomicile_codes" in result

    @pytest.mark.parametrize(
        "columns,row_source,row_db,expected_changed_field,expected_diff_type",
        [
            (  # identical NaNs
                {"latitude", "longitude"},
                {"latitude": np.nan, "longitude": np.nan},
                {"latitude": np.nan, "longitude": np.nan},
                None,
                None,
            ),
            (  # NaN vs value
                {"latitude"},
                {"latitude": 48.8566},
                {"latitude": np.nan},
                "latitude",
                [1, 0, 0],
            ),
            (  # different values
                {"latitude"},
                {"latitude": 48.8566},
                {"latitude": 48.8567},
                "latitude",
                [1, 0, 0],
            ),
            (  # identical values
                {"latitude"},
                {"latitude": 48.8566},
                {"latitude": 48.8566},
                None,
                None,
            ),
        ],
        ids=["nan_values", "nan_and_value", "different_values", "same_values"],
    )
    def test_field_changed_float(
        self, columns, row_source, row_db, expected_changed_field, expected_diff_type
    ):
        """Test field_changed with float values"""
        comparator = ActeurComparator(columns)
        result = comparator.field_changed(row_source, row_db)

        if expected_changed_field is None:
            assert result == {}
        else:
            assert expected_changed_field in result
            assert result[expected_changed_field] == expected_diff_type

    def test_field_changed_metadata_accumulation(self):
        """Test that metadata accumulates correctly"""
        comparator = ActeurComparator({"nom"})

        # First change
        row_source1 = {"nom": "Acteur 1 modifié"}
        row_db1 = {"nom": "Acteur 1"}
        comparator.field_changed(row_source1, row_db1)

        # Second change
        row_source2 = {"nom": "Acteur 2 modifié"}
        row_db2 = {"nom": "Acteur 2"}
        comparator.field_changed(row_source2, row_db2)

        assert "nom" in comparator.metadata
        assert comparator.metadata["nom"].modif == 2

    def test_field_changed_multiple_columns(self):
        """Test field_changed with multiple columns"""
        comparator = ActeurComparator({"nom", "email", "telephone"})
        row_source = {
            "nom": "Acteur 1 modifié",
            "email": "test@example.com",
            "telephone": "0123456789",
        }
        row_db = {
            "nom": "Acteur 1",
            "email": "test@example.com",
            "telephone": "0987654321",
        }

        result = comparator.field_changed(row_source, row_db)
        assert "nom" in result
        assert "telephone" in result
        assert "email" not in result
        assert len(result) == 2

    def test_field_changed_mixed_types(self):
        """Test field_changed with different types of changes"""
        comparator = ActeurComparator({"nom", "email", "adresse"})
        row_source = {
            "nom": "Acteur 1",  # No change
            "email": "nouveau@example.com",  # Addition
            "adresse": "",  # Deletion
        }
        row_db = {
            "nom": "Acteur 1",
            "email": "",
            "adresse": "123 Rue Test",
        }

        result = comparator.field_changed(row_source, row_db)
        assert "email" in result
        assert result["email"] == [0, 0, 1]  # AJOUT (addition)
        assert "adresse" in result
        assert result["adresse"] == [0, 1, 0]  # SUP (deletion)
        assert "nom" not in result

    def test_field_changed_empty_columns_to_compare(self):
        """Test field_changed with no columns to compare"""
        comparator = ActeurComparator(set())
        row_source = {"nom": "Acteur 1"}
        row_db = {"nom": "Acteur 2"}

        result = comparator.field_changed(row_source, row_db)
        assert result == {}
        assert comparator.metadata == {}
