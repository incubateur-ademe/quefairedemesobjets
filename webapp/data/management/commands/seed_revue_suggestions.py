"""Deterministic dataset for the SOURCE suggestions review screen.

**For tests only** (pytest, Playwright e2e): the command refuses to run outside a
test database (see `check_test_database`).

Creates, with the prefix `seed_revue_`:
- a SOURCE_MODIFICATION cohorte with more than 100 groupes and 500 lignes
  (to exercise pagination and « select all matching the filter »),
- a SOURCE_AJOUT cohorte and a SOURCE_SUPPRESSION cohorte,
- the acteurs, corrections (RevisionActeur) and parents they rely on,
- mixed statuts and SuggestionLog of every level.

Running the command again replaces the previous seed.
"""

import random

from data.models.suggestion import (
    SuggestionAction,
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionLog,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.services.suggestion_statut import recompute_cohorte_statut
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from qfdmo.models.acteur import (
    Acteur,
    ActeurStatus,
    ActeurType,
    RevisionActeur,
    Source,
)

PREFIX = "seed_revue_"
# Databases on which the seed may run: pytest test databases (`test_` prefix) and
# the Playwright e2e database (DB_WEBAPP_SAMPLE)
E2E_DATABASE_NAMES = ["webapp_sample"]
FORBIDDEN_ENVIRONMENTS = ["production", "staging", "preprod"]
NB_GROUPES_MODIFICATION = 140
NB_GROUPES_AJOUT = 20
NB_GROUPES_SUPPRESSION = 15

NOMS = [
    "Ressourcerie",
    "Recyclerie",
    "Repair café",
    "Cordonnerie",
    "Emmaüs",
    "Bricothèque",
    "Atelier vélo",
    "Friperie",
    "Électroménager d'occasion",
    "Librairie solidaire",
]
VILLES = [
    ("Paris", "75011", 48.857, 2.379),
    ("Lyon", "69003", 45.760, 4.850),
    ("Nantes", "44000", 47.218, -1.553),
    ("Lille", "59000", 50.629, 3.057),
    ("Montpellier", "34000", 43.610, 3.876),
    ("Besançon", "25000", 47.237, 6.024),
    ("Orléans", "45000", 47.902, 1.909),
    ("Saint-Étienne", "42000", 45.439, 4.387),
]
RUES = ["rue de la Paix", "avenue Jean Jaurès", "boulevard Voltaire", "place du Marché"]
CHAMPS_MODIFIABLES = [
    ["nom"],
    ["latitude", "longitude"],
    ["adresse"],
    ["code_postal"],
    ["ville"],
    ["url"],
    ["telephone"],
    ["email"],
    ["siret"],
    ["siren"],
    ["horaires_description"],
]
LOGS = [
    (SuggestionLog.SuggestionLogLevel.INFO, "Normalisation des numéros de téléphone"),
    (SuggestionLog.SuggestionLogLevel.WARNING, "Code postal déduit de la ville"),
    (SuggestionLog.SuggestionLogLevel.ERROR, "SIRET invalide, champ ignoré"),
]


def check_test_database():
    """Guard: the seed deletes and creates acteurs, it must never run on a real
    database."""
    if settings.ENVIRONMENT in FORBIDDEN_ENVIRONMENTS:
        raise CommandError(
            f"seed_revue_suggestions est interdit en environnement "
            f"« {settings.ENVIRONMENT} »"
        )
    database_name = connection.settings_dict["NAME"]
    if not (database_name.startswith("test_") or database_name in E2E_DATABASE_NAMES):
        raise CommandError(
            "seed_revue_suggestions est réservé aux tests : base de données "
            f"« {database_name} » refusée (attendu : test_* ou "
            f"{', '.join(E2E_DATABASE_NAMES)})"
        )


class Command(BaseCommand):
    help = (
        "Tests only: create a deterministic dataset of SOURCE suggestions for the "
        "review screen"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Only delete the previous seed, without creating a new one",
        )

    def handle(self, *args, **options):
        check_test_database()
        with transaction.atomic():
            self.delete_seed()
            if options["reset"]:
                self.stdout.write("Seed supprimé")
                return
            self.rng = random.Random(42)
            self.reviewer = User.objects.filter(is_superuser=True).first()
            self.acteur_type = ActeurType.objects.order_by("id").first() or (
                ActeurType.objects.create(code=f"{PREFIX}type", libelle="Commerce")
            )
            self.source, _ = Source.objects.get_or_create(
                code=f"{PREFIX}source", defaults={"libelle": "Seed revue"}
            )
            cohortes = [
                self.create_modification_cohorte(),
                self.create_ajout_cohorte(),
                self.create_suppression_cohorte(),
            ]
            recompute_cohorte_statut([cohorte.id for cohorte in cohortes])

        for cohorte in cohortes:
            nb_groupes = cohorte.suggestion_groupes.count()
            nb_lignes = (
                SuggestionUnitaire.objects.filter(
                    suggestion_groupe__suggestion_cohorte=cohorte
                )
                .values("suggestion_groupe_id", "champs")
                .distinct()
                .count()
            )
            self.stdout.write(
                f"Cohorte {cohorte.id} {cohorte.type_action} : "
                f"{nb_groupes} groupes, {nb_lignes} lignes"
            )

    # --- Deletion ---

    def delete_seed(self):
        SuggestionCohorte.objects.filter(identifiant_action__startswith=PREFIX).delete()
        RevisionActeur.objects.filter(identifiant_unique__startswith=PREFIX).update(
            parent=None
        )
        RevisionActeur.objects.filter(identifiant_unique__startswith=PREFIX).delete()
        Acteur.objects.filter(identifiant_unique__startswith=PREFIX).delete()

    # --- Acteurs ---

    def acteur_values(self, index: int) -> dict:
        ville, code_postal, lat, lng = VILLES[index % len(VILLES)]
        siren = f"{100000000 + index * 7919:09d}"
        return {
            "nom": f"{NOMS[index % len(NOMS)]} {ville} {index}",
            "adresse": f"{index + 1} {RUES[index % len(RUES)]}",
            "code_postal": code_postal,
            "ville": ville,
            "url": f"https://acteur-{index}.example.org",
            "telephone": f"01 23 45 {index % 100:02d} {(index * 3) % 100:02d}",
            "email": f"contact{index}@example.org",
            "siren": siren,
            "siret": f"{siren}{index % 100000:05d}",
            "horaires_description": "Du lundi au samedi, 10h-18h",
            "latitude": f"{lat + (index % 50) / 1000:.5f}",
            "longitude": f"{lng + (index % 30) / 1000:.5f}",
        }

    def suggested_value(self, champ: str, current: dict, index: int) -> str:
        if champ == "nom":
            return current["nom"].upper()
        if champ == "latitude":
            return f"{float(current['latitude']) + 0.002:.5f}"
        if champ == "longitude":
            return f"{float(current['longitude']) - 0.002:.5f}"
        if champ == "url":
            return f"https://www.acteur-{index}.example.fr"
        if champ == "telephone":
            return current["telephone"].replace(" ", "")
        if champ == "email":
            return f"bonjour{index}@example.fr"
        if champ == "siret":
            return f"{current['siren']}{(index + 1) % 100000:05d}"
        if champ == "siren":
            return f"{100000000 + index * 7919 + 1:09d}"
        if champ == "code_postal":
            return current["code_postal"][:-1] + "1"
        if champ == "ville":
            return current["ville"].upper()
        if champ == "adresse":
            return current["adresse"] + " bis"
        return f"{current.get(champ, '')} (mis à jour)"

    def build_acteur(self, model, identifiant_unique: str, values: dict):
        return model(
            identifiant_unique=identifiant_unique,
            identifiant_externe=identifiant_unique.removeprefix(PREFIX),
            acteur_type=self.acteur_type,
            source=self.source,
            statut=ActeurStatus.ACTIF,
            location=Point(float(values["longitude"]), float(values["latitude"])),
            **{
                key: value
                for key, value in values.items()
                if key not in ("latitude", "longitude")
            },
        )

    # --- Cohortes ---

    def create_cohorte(self, type_action: str, name: str) -> SuggestionCohorte:
        cohorte = SuggestionCohorte.objects.create(
            identifiant_action=f"{PREFIX}{name}",
            identifiant_execution=f"manual__2026-10-01T06:00:00+00:00_{name}",
            type_action=type_action,
            metadata={"source_code": self.source.code, "nb_acteurs": 0},
        )
        for niveau, message in LOGS:
            SuggestionLog.objects.create(
                suggestion_cohorte=cohorte,
                niveau_de_log=niveau,
                fonction_de_transformation="seed_revue",
                message=message,
            )
        return cohorte

    def pick_statut(self) -> str:
        draw = self.rng.random()
        if draw < 0.70:
            return SuggestionStatut.AVALIDER
        if draw < 0.82:
            return SuggestionStatut.ATRAITER
        if draw < 0.90:
            return SuggestionStatut.REJETEE
        if draw < 0.96:
            return SuggestionStatut.SUCCES
        return SuggestionStatut.ERREUR

    def decision(self, statut: str) -> dict:
        if statut in (SuggestionStatut.AVALIDER,):
            return {}
        return {"decision_par": self.reviewer, "decision_le": timezone.now()}

    def create_modification_cohorte(self) -> SuggestionCohorte:
        cohorte = self.create_cohorte(
            SuggestionAction.SOURCE_MODIFICATION, "modification"
        )
        acteurs, revisions, parents = [], [], []
        groupes_specs = []
        for index in range(NB_GROUPES_MODIFICATION):
            identifiant_unique = f"{PREFIX}{index:04d}"
            values = self.acteur_values(index)
            acteurs.append(self.build_acteur(Acteur, identifiant_unique, values))
            has_parent = index % 5 == 0
            has_revision = has_parent or index % 3 == 0
            parent_id = f"{PREFIX}parent_{index:04d}" if has_parent else None
            if has_parent:
                parent_values = self.acteur_values(index)
                parents.append(
                    self.build_acteur(RevisionActeur, parent_id, parent_values)
                )
            if has_revision:
                revision = self.build_acteur(RevisionActeur, identifiant_unique, values)
                revision.parent_id = parent_id
                revisions.append(revision)
            groupes_specs.append(
                (index, identifiant_unique, values, has_revision, parent_id)
            )

        Acteur.objects.bulk_create(acteurs)
        RevisionActeur.objects.bulk_create(parents)
        RevisionActeur.objects.bulk_create(revisions)

        for index, identifiant_unique, values, has_revision, parent_id in groupes_specs:
            statut = self.pick_statut()
            groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte,
                statut=statut,
                acteur_id=identifiant_unique,
                revision_acteur_id=identifiant_unique if has_revision else None,
                parent_revision_acteur_id=parent_id,
                contexte={"source_code": self.source.code, "ligne": index},
                **self.decision(statut),
            )
            nb_lignes = self.rng.randint(3, 6)
            champs_list = self.rng.sample(CHAMPS_MODIFIABLES, nb_lignes)
            # Partially validated groupes: some lignes already validated
            nb_validated = (
                self.rng.randint(1, nb_lignes - 1)
                if statut == SuggestionStatut.AVALIDER and self.rng.random() < 0.15
                else 0
            )
            unitaires = []
            for position, champs in enumerate(champs_list):
                ligne_statut = (
                    SuggestionStatut.ATRAITER if position < nb_validated else statut
                )
                valeurs = [
                    self.suggested_value(champ, values, index) for champ in champs
                ]
                common = {
                    "suggestion_groupe": groupe,
                    "statut": ligne_statut,
                    "champs": champs,
                    "ordre": position + 1,
                    **self.decision(ligne_statut),
                }
                unitaires.append(
                    SuggestionUnitaire(
                        suggestion_modele="Acteur",
                        acteur_id=identifiant_unique,
                        valeurs=valeurs,
                        **common,
                    )
                )
                if has_revision and position == 0:
                    unitaires.append(
                        SuggestionUnitaire(
                            suggestion_modele="RevisionActeur",
                            revision_acteur_id=identifiant_unique,
                            valeurs=valeurs,
                            **common,
                        )
                    )
                if parent_id and position == 1:
                    unitaires.append(
                        SuggestionUnitaire(
                            suggestion_modele="ParentRevisionActeur",
                            parent_revision_acteur_id=parent_id,
                            valeurs=valeurs,
                            **common,
                        )
                    )
            SuggestionUnitaire.objects.bulk_create(unitaires)
        return cohorte

    def create_ajout_cohorte(self) -> SuggestionCohorte:
        cohorte = self.create_cohorte(SuggestionAction.SOURCE_AJOUT, "ajout")
        for offset in range(NB_GROUPES_AJOUT):
            index = 1000 + offset
            identifiant_unique = f"{PREFIX}nouveau_{index:04d}"
            values = self.acteur_values(index)
            groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte,
                contexte={"source_code": self.source.code, "ligne": index},
            )
            champs_list = [
                ["identifiant_unique"],
                ["nom"],
                ["adresse"],
                ["code_postal"],
                ["ville"],
                ["latitude", "longitude"],
                ["siret"],
                ["url"],
            ]
            values = {**values, "identifiant_unique": identifiant_unique}
            SuggestionUnitaire.objects.bulk_create(
                SuggestionUnitaire(
                    suggestion_groupe=groupe,
                    suggestion_modele="Acteur",
                    acteur_id=identifiant_unique,
                    champs=champs,
                    valeurs=[values[champ] for champ in champs],
                    ordre=position + 1,
                )
                for position, champs in enumerate(champs_list)
            )
        return cohorte

    def create_suppression_cohorte(self) -> SuggestionCohorte:
        cohorte = self.create_cohorte(
            SuggestionAction.SOURCE_SUPPRESSION, "suppression"
        )
        # Acteurs of the modification cohorte which disappeared from the source
        for index in range(NB_GROUPES_SUPPRESSION):
            identifiant_unique = f"{PREFIX}{index * 7:04d}"
            groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte,
                acteur_id=identifiant_unique,
                contexte={"source_code": self.source.code},
            )
            SuggestionUnitaire.objects.create(
                suggestion_groupe=groupe,
                suggestion_modele="Acteur",
                acteur_id=identifiant_unique,
                champs=["statut"],
                valeurs=[ActeurStatus.SUPPRIME],
            )
        return cohorte
