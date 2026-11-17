class TurboFrameMixin:
    """Renders a bare layout for Turbo Frame requests: Turbo only extracts
    the matching frame."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        in_frame = bool(self.request.headers.get("Turbo-Frame"))
        context["base_template"] = (
            "ui/layout/turbo.html" if in_frame else "ui/layout/assistant.html"
        )
        return context
