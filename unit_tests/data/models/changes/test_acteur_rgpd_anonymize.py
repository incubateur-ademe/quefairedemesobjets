import json
import re

import pytest
from django.contrib.gis.geos import Point

from data.models.changes.acteur_rgpd_anonymize import (
    VALUE_ANONYMIZED,
    ChangeActeurRgpdAnonymize,
    rgpd_data_get,
)
from qfdmo.models.acteur import Acteur, ActeurStatus, ActeurType, RevisionActeur

TEST_DATA = {
    "location": Point(1, 2),
    "nom": "🟠 not anonymized",
    "nom_officiel": "🟠 not anonymized",
    "nom_commercial": "🟠 not anonymized",
    "description": "🟠 not anonymized",
    "email": "me@myself.com",
    "telephone": "🟠 not anonymized",
    "adresse": "🟠 not anonymized",
    "adresse_complement": "🟠 not anonymized",
    "statut": ActeurStatus.ACTIF,
    "commentaires": "  ",
}

COMMENT_PATTERN = (
    VALUE_ANONYMIZED + r" via suggestion du \d{4}-\d{2}-\d{2} à \d{2}:\d{2}:\d{2} UTC"
)


@pytest.mark.django_db
class TestChangeActeurRgpdAnonymize:
    def test_name(self):
        assert ChangeActeurRgpdAnonymize.name() == "acteur_rgpd_anonymize"

    def test_raise_if_acteur_does_not_exist(self):
        change = ChangeActeurRgpdAnonymize(id="dummy")
        with pytest.raises(Acteur.DoesNotExist):
            change.apply()

    def test_working_only_in_base(self):
        # We start by creating acteur only in base
        at1 = ActeurType.objects.create(code="at1")
        id1 = "id1"
        data = TEST_DATA.copy()
        data["acteur_type"] = at1
        data["identifiant_unique"] = id1
        Acteur.objects.create(**data)

        # We check that acteur isn't in revision yet
        assert RevisionActeur.objects.filter(pk=id1).count() == 0

        # Since RGPD changes are to owerwrite consistently, we don't
        # pass any data to the model, only the ID of the acteur
        # and the model takes care of the rest
        data_expected = rgpd_data_get()
        ChangeActeurRgpdAnonymize(id=id1, data=data_expected).apply()

        # We check that no revision was created because we overwrite
        # hence don't want Revisions meants for versioning
        assert not RevisionActeur.objects.filter(pk=id1).exists()

        # We check that acteur in base was anonymized
        base = Acteur.objects.get(pk=id1)
        for key, value in data_expected.items():
            # dynamic, tested further below
            if key == "commentaires":
                continue
            assert getattr(base, key) == value  # static

        # Comments
        comments = json.loads(base.commentaires)
        assert re.match(COMMENT_PATTERN, comments[0]["message"])

        # We check that other fields were not modified
        assert base.description == "🟠 not anonymized"

    def test_working_both_base_and_revision(self):
        # We start by creating acteur BOTH in base and revision
        at1 = ActeurType.objects.create(code="at1")
        id2 = "id2"
        data = TEST_DATA.copy()
        data["acteur_type"] = at1
        data["identifiant_unique"] = id2
        Acteur.objects.create(**data)
        RevisionActeur.objects.create(**data)

        # Same remark as previous test on not having to pass data
        data_expected = rgpd_data_get()
        ChangeActeurRgpdAnonymize(id=id2, data=data_expected).apply()

        # In this case we check that all instances were anonymized
        instances = [
            Acteur.objects.get(pk=id2),
            RevisionActeur.objects.get(pk=id2),
        ]
        for instance in instances:
            for key, value in data_expected.items():
                # dynamic, tested further below
                if key == "commentaires":
                    continue
                assert getattr(instance, key) == value  # static
            assert instance.description == "🟠 not anonymized"

            # Comments
            comments = json.loads(instance.commentaires)
            assert re.match(COMMENT_PATTERN, comments[0]["message"])
