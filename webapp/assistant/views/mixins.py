class TurboFrameMixin:
    """Serves a reduced template when the request comes from a Turbo Frame.

    Turbo only extracts the matching frame from the response: rendering the
    full layout would be wasted work, and HTML transferred for nothing on
    every interaction.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        in_frame = bool(self.request.headers.get("Turbo-Frame"))
        context["in_frame"] = in_frame
        context["base_template"] = (
            "ui/layout/turbo.html" if in_frame else "ui/layout/assistant.html"
        )
        return context
