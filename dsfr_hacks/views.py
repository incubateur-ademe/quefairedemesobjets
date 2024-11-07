from django.views.generic.edit import FormView

from dsfr_hacks.colors import DSFRColors
from dsfr_hacks.forms import ColorForm


class ColorsView(FormView):
    form_class = ColorForm

    def form_valid(self, form):
        for name, hexa in DSFRColors.iteritems():
            if hexa == form.cleaned_data.hexa_color:
                form.cleaned_data.dsfr_color = name

        return super().form_valid(form)
