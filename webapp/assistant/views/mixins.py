class TurboFrameMixin:
    """Sert un gabarit réduit quand la requête vient d'un Turbo Frame.

    Turbo n'extrait que le frame correspondant de la réponse : rendre le
    layout complet serait du travail jeté, et du HTML transféré pour rien à
    chaque interaction.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["base_template"] = (
            "ui/layout/turbo.html"
            if self.request.headers.get("Turbo-Frame")
            else "ui/layout/assistant.html"
        )
        return context
