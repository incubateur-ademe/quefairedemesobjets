import pytest

from qfdmo.admin.acteur import OpenSourceDisplayedActeurResource
from qfdmo.models.acteur import DataLicense
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    SourceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


@pytest.mark.django_db
class TestOpenSourceDisplayedActeurResource:

    def test_export_columns(self):
        DisplayedActeurFactory.create_batch(11)

        dataset = OpenSourceDisplayedActeurResource().export()

        assert len(dataset) == 11
        for row in dataset.dict:
            assert list(row.keys()) == [
                "Identifiant",
                "Paternité",
                "Nom",
                "Nom commercial",
                "SIREN",
                "SIRET",
                "Description",
                "Type d'acteur",
                "Site web",
                "Téléphone",
                "Adresse",
                "Complément d'adresse",
                "Code postal",
                "Ville",
                "latitude",
                "longitude",
                "Qualités et labels",
                "Public accueilli",
                "Reprise",
                "Exclusivité de reprise/réparation",
                "Uniquement sur RDV",
                "Date de dernière modification",
                "Type de services",
                "Propositions de services",
            ]

    @pytest.mark.parametrize(
        "telephone, expected_telephone",
        [
            ("0123456789", "0123456789"),
            ("01 23 45 67 89", "01 23 45 67 89"),
            ("0223456789", "0223456789"),
            ("0323456789", "0323456789"),
            ("0423456789", "0423456789"),
            ("0523456789", "0523456789"),
            ("0623456789", None),
            ("06 23 45 67 89", None),
            ("0723456789", None),
            ("0823456789", "0823456789"),
            ("0923456789", "0923456789"),
        ],
    )
    def test_export_telephone(self, telephone, expected_telephone):
        DisplayedActeurFactory.create(telephone=telephone)

        dataset = OpenSourceDisplayedActeurResource().export()

        dataset_dict = dataset.dict
        assert dataset_dict[0]["Téléphone"] == expected_telephone

    def test_propositions_de_services(self):
        displayedacteur = DisplayedActeurFactory()
        action = ActionFactory(code="action", libelle="Action")
        sscat1 = SousCategorieObjetFactory(
            code="sous_categorie_1", libelle="Sous catégorie 1"
        )
        sscat2 = SousCategorieObjetFactory(
            code="sous_categorie_2", libelle="Sous catégorie 2"
        )
        proposition_services = DisplayedPropositionServiceFactory(
            acteur=displayedacteur,
            action=action,
        )
        proposition_services.sous_categories.set([sscat1, sscat2])

        dataset = OpenSourceDisplayedActeurResource().export()

        dataset_dict = dataset.dict
        expected_propositions_de_services = (
            '[{"action":"action","sous_categories":["sous_categorie_1",'
            '"sous_categorie_2"]}]'
        )
        assert (
            dataset_dict[0]["Propositions de services"]
            == expected_propositions_de_services
        )

    @pytest.mark.parametrize(
        "source_data, expected_other_contributeurs",
        [
            (
                [],
                [],
            ),
            (
                [
                    {"libelle": "Source 1", "code": "source1"},
                    {"libelle": "Source 2", "code": "source2"},
                ],
                ["Source 1", "Source 2"],
            ),
            (
                [
                    {"libelle": "Source 1", "code": "source1"},
                    {"libelle": "Source 2", "code": "source2"},
                    {"libelle": "Source 1", "code": "source3"},
                ],
                ["Source 1", "Source 2"],
            ),
        ],
    )
    def test_sources(self, source_data, expected_other_contributeurs):
        displayedacteur = DisplayedActeurFactory()
        sources = [SourceFactory(**data) for data in source_data]
        displayedacteur.sources.set(sources)

        dataset = OpenSourceDisplayedActeurResource().export()

        dataset_dict = dataset.dict

        contributeurs = dataset_dict[0]["Paternité"].split("|")
        assert contributeurs[0] == "Longue Vie Aux Objets"
        assert contributeurs[1] == "ADEME"
        assert sorted(contributeurs[2:]) == sorted(expected_other_contributeurs)

    def test_filter_by_licenses(self):
        source_open_licence = SourceFactory(licence=DataLicense.OPEN_LICENSE.value)
        source_cc_by_nc_sa = SourceFactory(licence=DataLicense.CC_BY_NC_SA.value)
        acteur_open_license = DisplayedActeurFactory()
        acteur_open_license.sources.set([source_open_licence])
        acteur_multi_licences = DisplayedActeurFactory()
        acteur_multi_licences.sources.set([source_open_licence, source_cc_by_nc_sa])
        acteur_cc_license = DisplayedActeurFactory.create()
        acteur_cc_license.sources.set([source_cc_by_nc_sa])

        dataset = OpenSourceDisplayedActeurResource(
            licenses=[DataLicense.OPEN_LICENSE.value, DataLicense.CC_BY_NC_SA.value]
        ).export()

        identifiants = [row["Identifiant"] for row in dataset.dict]
        assert len(dataset) == 3
        assert acteur_open_license.uuid in identifiants
        assert acteur_multi_licences.uuid in identifiants
        assert acteur_cc_license.uuid in identifiants

        dataset = OpenSourceDisplayedActeurResource(
            licenses=[DataLicense.OPEN_LICENSE.value]
        ).export()

        identifiants = [row["Identifiant"] for row in dataset.dict]
        assert len(dataset) == 2
        assert acteur_open_license.uuid in identifiants
        assert acteur_multi_licences.uuid in identifiants

        # test acteur_multi doesn't refer license CC_BY_NC_SA
        row_multi = next(
            row
            for row in dataset.dict
            if row["Identifiant"] == acteur_multi_licences.uuid
        )
        assert row_multi["Identifiant"] == acteur_multi_licences.uuid
        assert (
            row_multi["Paternité"]
            == f"Longue Vie Aux Objets|ADEME|{source_open_licence.libelle}"
        )

        dataset = OpenSourceDisplayedActeurResource(
            licenses=[DataLicense.CC_BY_NC_SA.value]
        ).export()

        identifiants = [row["Identifiant"] for row in dataset.dict]
        assert len(dataset) == 2
        assert acteur_multi_licences.uuid in identifiants
        assert acteur_cc_license.uuid in identifiants
