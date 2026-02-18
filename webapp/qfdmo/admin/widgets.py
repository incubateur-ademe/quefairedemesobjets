from django import forms


class SousCategorieChoiceWidget(forms.SelectMultiple):
    def create_option(self, name, value, *args, **kwargs):
        option = super().create_option(name, value, *args, **kwargs)
        if value:
            option["attrs"]["data-categorie"] = value.instance.categorie.pk
        return option


class CategorieChoiceWidget(forms.SelectMultiple):
    def create_option(self, name, value, *args, **kwargs):
        option = super().create_option(name, value, *args, **kwargs)
        if value:
            option["attrs"]["data-admin-categorie-widget-target"] = "option"
        return option

    class Media:
        js = ("admin-categorie-widget.js",)
