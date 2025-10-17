from django.core.validators import EmailValidator

EMPTY_ACTEUR_FIELD = "__empty__"


class EmptyValidator:
    def __call__(self, value):
        if value == EMPTY_ACTEUR_FIELD:
            return
        super().__call__(value)


class EmptyEmailValidator(EmptyValidator, EmailValidator):
    pass
