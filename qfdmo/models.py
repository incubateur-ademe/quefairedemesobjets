from django.db import models
from unidecode import unidecode


class CategoryManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Category(models.Model):
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    objects = CategoryManager()

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)


class SubCategoryManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class SubCategory(models.Model):
    class Meta:
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"

    objects = SubCategoryManager()

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    lvao_id = models.IntegerField(blank=True, null=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, blank=True, null=True
    )
    code = models.CharField(max_length=10, unique=True, blank=False, null=False)

    @property
    def sanitized_name(self):
        return unidecode(self.name).upper()

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)
