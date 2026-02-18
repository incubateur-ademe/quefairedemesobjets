import unicodedata
from io import BytesIO
from pathlib import Path

import willow
from django.conf import settings
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from wagtail.images.models import Image

from qfdmd.models import Produit


class Command(BaseCommand):
    help = "Renommage des infotris à partir du travail de Lucas"

    def copy(self, source, target):
        target.write_bytes(source.read_bytes())

    def create_wagtail_image(self, path, produit):
        img_bytes = path.read_bytes()
        filename = path.name
        with path.open(mode="rb") as f:
            img_file = ImageFile(BytesIO(img_bytes), name=filename)
            im = willow.Image.open(f)
            width, height = im.get_size()
            img_obj = Image(
                title=f"Infotri pour {produit.nom}",
                file=img_file,
                width=width,
                height=height,
            )
            img_obj.save()
            return img_obj

    def import_pictos(self):
        infotris = Path(settings.BASE_DIR / "infotris" / "final")
        # TODO: sort
        for path in infotris.iterdir():
            id = path.name.split(".")[0]
            if "_" in id:
                # TODO: translate in english
                # Dans le cas où le nom de fichier comporte un index, par
                # exemple 123_1.svg, on l'ignore et on considère que le tri
                # alphabétiques des fichiers suffit à sa prise en compte.
                id = id.split("_")[0]

            produit = Produit.objects.get(id=id)
            image = self.create_wagtail_image(path, produit)
            produit.infotri.append(("image", image))
            produit.save()

    def rename_pictos(self):
        infotris = Path(settings.BASE_DIR / "infotris")
        for path in infotris.iterdir():
            # Prevent error when filename contains accent on MacOS
            # See https://stackoverflow.com/questions/26732985/utf-8-and-os-listdir/26733055#26733055
            filename = unicodedata.normalize("NFC", path.name.split(".")[0])

            if (path.is_dir()) or not filename:
                continue

            try:
                # We first test if the filename matches a synonyme
                synonyme = Produit.objects.get(nom=filename)
                self.copy(
                    path,
                    Path(
                        settings.BASE_DIR
                        / "infotris"
                        / "final"
                        / f"{synonyme.id}{path.suffix}"
                    ),
                )
                continue
            except Produit.DoesNotExist:
                pass

            try:
                # Then if it is a prefix...in some cases the filename was truncated
                synonyme = Produit.objects.get(nom__startswith=filename)
                self.copy(
                    path,
                    Path(
                        settings.BASE_DIR
                        / "infotris"
                        / "final"
                        / f"{synonyme.id}{path.suffix}"
                    ),
                )
                continue
            except Produit.DoesNotExist:
                pass

            try:
                # Then we try to replace colon as they might be used instead of slashes
                synonyme = Produit.objects.get(
                    nom__startswith=filename.replace(":", "/")
                )
                self.copy(
                    path,
                    Path(
                        settings.BASE_DIR
                        / "infotris"
                        / "final"
                        / f"{synonyme.id}{path.suffix}"
                    ),
                )
                continue
            except Produit.DoesNotExist:
                pass

            try:
                # Finally, we check if it contains a number, meaning the matching
                # synonyme has several infotris
                nom = filename.split("_")[0]
                index = filename.split("_")[1]
                synonyme = Produit.objects.get(nom=nom)

                self.copy(
                    path,
                    Path(
                        settings.BASE_DIR
                        / "infotris"
                        / "final"
                        / f"{synonyme.id}_{index}{path.suffix}"
                    ),
                )
                continue
            except (IndexError, Produit.DoesNotExist):
                pass

            self.stdout.write(self.style.ERROR(filename))

    def handle(self, *args, **options):
        self.rename_pictos()
        self.import_pictos()
        self.stdout.write(self.style.SUCCESS("Import des infotris terminé"))
