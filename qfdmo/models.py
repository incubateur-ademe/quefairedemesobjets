from django.db import models
from unidecode import unidecode


class NameAsNaturalKeyManager(models.Manager):
    def get_by_natural_key(self, name: str) -> models.Model:
        return self.get(name=name)


class NameAsNaturalKeyModel(models.Model):
    class Meta:
        abstract = True

    objects = NameAsNaturalKeyManager()

    name = models.CharField()

    def natural_key(self) -> tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name


class Category(NameAsNaturalKeyModel):
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    objects = NameAsNaturalKeyManager()

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)


class SubCategory(NameAsNaturalKeyModel):
    class Meta:
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"

    objects = NameAsNaturalKeyManager()

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, blank=True, null=True
    )
    code = models.CharField(max_length=10, unique=True, blank=False, null=False)

    @property
    def sanitized_name(self) -> str:
        return unidecode(self.name).upper()


class Action(NameAsNaturalKeyModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class Activity(NameAsNaturalKeyModel):
    class Meta:
        verbose_name_plural = "Activities"

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class EntityType(NameAsNaturalKeyModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return self.name
