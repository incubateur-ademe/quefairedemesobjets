import json
import re

import pandas as pd
import pytest
from django.contrib.gis.geos import Point
from rich import print

from dags.enrich.config import COLS
from dags.enrich.tasks.business_logic.enrich_ae_rgpd_suggest import (
    enrich_ae_rgpd_suggest,
)

CHANGE_ANON = "ANONYMISE POUR RAISON RGPD"
COMMENT_PATTERN = CHANGE_ANON + r" le \d{4}-\d{2}-\d{2} à \d{2}:\d{2}:\d{2} UTC"


@pytest.mark.django_db
class TestEnrichAeRgpdSuggest:

    @pytest.fixture
    def df(self):
        return pd.DataFrame(
            {
                COLS.ACTEUR_ID: ["id1", "id2"],
                COLS.ACTEUR_NOMS_ORIGINE: ["acteur1", "acteur2"],
                COLS.MATCH_WORDS: ["acteur1", "acteur2"],
                COLS.MATCH_SCORE: [1.0, 1.0],
                COLS.ACTEUR_SIRET: ["11111111100001", "22222222200001"],
            }
        )

    @pytest.fixture
    def acteurs(self, df):
        from qfdmo.models import Acteur, ActeurType

        at1 = ActeurType(code="at1")
        at1.save()

        for _, row in df.iterrows():
            Acteur.objects.create(
                # Required fields
                identifiant_unique=row[COLS.ACTEUR_ID],
                acteur_type=at1,
                location=Point(1, 2),
                # Fields to anonymize
                nom=row[COLS.ACTEUR_NOMS_ORIGINE],
                nom_officiel="🟠 not anonymized",
                nom_commercial="🟠 not anonymized",
                email="me@myself.com",
                telephone="🟠 not anonymized",
                adresse="🟠 not anonymized",
                adresse_complement="🟠 not anonymized",
                # Fields to keep as-is
                description="🟠 not anonymized",
            )

    @pytest.fixture
    def suggestions(self, df, acteurs):
        return enrich_ae_rgpd_suggest(
            df=df,
            identifiant_action="my_action_id",
            identifiant_execution="my_execution_id",
            dry_run=True,
        )

    @pytest.fixture
    def suggest(self, suggestions) -> dict:
        suggest = suggestions[0]
        print(f"{suggest=}")
        return suggest

    def test_one_suggestion_per_acteur(self, df, suggestions):
        assert len(suggestions) == len(df)

    def test_one_change_per_suggestion(self, suggest):
        # 1 change per acteur, we don't group acteurs together
        # even if they have identical SIREN or SIRET
        assert len(suggest["suggestion"]["changes"]) == 1

    def test_suggestion_change(self, suggest):
        # The changes being sensitive, this test intentionnally
        # hardcodes the structure of the suggestion so we need
        # to udpate tests with intention when changing the DAG
        from data.models.change import SuggestionChange
        from qfdmo.models import Acteur, ActeurStatus

        change = suggest["suggestion"]["changes"][0]
        assert change["model_name"] == "acteur_rgpd_anonymize"
        assert change["model_params"] == {"id": "id1"}

        SuggestionChange(**change).apply()

        acteur = Acteur.objects.get(identifiant_unique="id1")

        # Fields anonymized
        assert acteur.nom == "ANONYMISE POUR RAISON RGPD"
        assert acteur.nom_officiel == "ANONYMISE POUR RAISON RGPD"
        assert acteur.nom_commercial == "ANONYMISE POUR RAISON RGPD"
        assert acteur.email == ""
        assert acteur.telephone == "ANONYMISE POUR RAISON RGPD"
        assert acteur.adresse == "ANONYMISE POUR RAISON RGPD"
        assert acteur.adresse_complement == "ANONYMISE POUR RAISON RGPD"

        # Status set to inactif
        assert acteur.statut == ActeurStatus.INACTIF

        # Check comment
        comments = json.loads(acteur.commentaires)
        assert re.match(COMMENT_PATTERN, comments[0]["message"])

        # Fields not changed
        assert acteur.description == "🟠 not anonymized"
        assert acteur.location.x == 1
        assert acteur.location.y == 2
        assert acteur.acteur_type.code == "at1"
