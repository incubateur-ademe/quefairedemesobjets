from django.core.validators import EmailValidator

from core.models.constants import EMPTY_ACTEUR_FIELD


class EmptyValidator:
    def __call__(self, value):

        if value == EMPTY_ACTEUR_FIELD:
            return
        super().__call__(value)


class EmptyEmailValidator(EmptyValidator, EmailValidator):
    pass
