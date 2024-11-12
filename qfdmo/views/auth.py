from django.contrib.auth.views import LoginView

from qfdmo.views.adresses import IframeMixin


class LVAOLoginView(IframeMixin, LoginView):
    pass
