from collections import defaultdict

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.forms import model_to_dict
from tqdm import tqdm

from qfdmo.models import LVAOBase, PropositionService, ReemploiActeur

STEP = 1000


class Command(BaseCommand):
    help = "From LVAO BASE, populate ReemploiActeur and its PropositionServices"

    def handle(self, *args, **options):
        total_lvao_bases = LVAOBase.objects.count()
        progress = tqdm(total=total_lvao_bases)
        lvao_bases = LVAOBase.objects.prefetch_related(
            "lvao_base_revisions",
            "lvao_base_revisions__acteur_services",
            "lvao_base_revisions__acteur_type",
            "lvao_base_revisions__actions",
            "lvao_base_revisions__sous_categories",
        ).all()
        count = 0
        offset = 0
        limit = STEP
        while offset < total_lvao_bases:
            for lvao_base in lvao_bases[offset:limit]:
                last_lvao_base_revision = lvao_base.lvao_base_revisions.order_by(
                    "lvao_revision_id"
                ).last()
                reemploi_acteur_fields = model_to_dict(
                    last_lvao_base_revision,
                    fields=[
                        "nom",
                        "acteur_type",
                        "adresse",
                        "adresse_complement",
                        "code_postal",
                        "ville",
                        "url",
                        "email",
                        "latitude",
                        "longitude",
                        "telephone",
                        "multi_base",
                        "nom_commercial",
                        "nom_officiel",
                        "manuel",
                        "label_reparacteur",
                        "siret",
                        "source_donnee",
                        "identifiant_externe",
                    ],
                )
                reemploi_acteur_fields["acteur_type_id"] = reemploi_acteur_fields[
                    "acteur_type"
                ]
                reemploi_acteur_fields["location"] = Point(
                    reemploi_acteur_fields["longitude"],
                    reemploi_acteur_fields["latitude"],
                )
                del reemploi_acteur_fields["longitude"]
                del reemploi_acteur_fields["latitude"]
                del reemploi_acteur_fields["acteur_type"]
                reemploi_acteur, _ = ReemploiActeur.objects.get_or_create(
                    identifiant_unique=lvao_base.identifiant_unique,
                    defaults=reemploi_acteur_fields,
                )
                action_acteurservice_set = defaultdict(defaultdict)
                for revision in lvao_base.lvao_base_revisions.all().order_by(
                    "lvao_revision_id"
                ):
                    for action in revision.actions.all():
                        for acteur_service in revision.acteur_services.all():
                            action_acteurservice_set[action.id][acteur_service.id] = {
                                "action": action,
                                "acteur_service": acteur_service,
                                "sous-categories": revision.sous_categories.all(),
                                "reemploi_acteur": reemploi_acteur,
                            }
                for action in action_acteurservice_set.values():
                    for action_acteurservice in action.values():
                        (
                            proposition_service,
                            _,
                        ) = PropositionService.objects.get_or_create(
                            action=action_acteurservice["action"],
                            acteur_service=action_acteurservice["acteur_service"],
                            reemploi_acteur=action_acteurservice["reemploi_acteur"],
                        )
                        proposition_service.sous_categories.all().delete()
                        for sous_categories in action_acteurservice["sous-categories"]:
                            proposition_service.sous_categories.add(sous_categories)

                count += 1
            offset += STEP
            limit += STEP
            progress.update(STEP)
        print(total_lvao_bases)
        print(count)
