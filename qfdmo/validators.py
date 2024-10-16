from django.core.validators import RegexValidator


class CodeValidator(RegexValidator):
    regex = r"^[a-z_]+$"
    message = (
        "Le champ `code` ne doit contenir que des caractères en minuscule et des"
        " underscores."
    )
    code = "invalid_code"
