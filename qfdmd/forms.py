from django import forms


class SearchForm(forms.Form):
    field_template_name = "components/search/search.html"
    search = forms.CharField(help_text="Entrez un objet ou un déchet")
