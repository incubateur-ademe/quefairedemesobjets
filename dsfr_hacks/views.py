from django.shortcuts import render
from django.views.generic.edit import FormView

from dsfr_hacks.colors import DSFRColors
from dsfr_hacks.forms import ColorForm


class ColorsView(FormView):
    template_name = "dsfr_hacks/colors.html"
    form_class = ColorForm

    def form_valid(self, form):
        dsfr_color = next(
            (
                key
                for key, val in DSFRColors.items()
                if form.cleaned_data["hexa_color"].lower() in val.lower()
            ),
            "Couleur introuvable",
        )

        return render(
            self.request,
            self.template_name,
            self.get_context_data(form=form, dsfr_color=dsfr_color),
        )
