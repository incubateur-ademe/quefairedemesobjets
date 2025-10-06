class ImportSourceException(Exception):
    """
    Base class for all exceptions raised during the import of source data
    """

    is_blocking = None


class ImportSourceValueError(Exception):
    """
    Exception type that forbid acteur insertion as a suggestion
    """

    is_blocking = True


class ImportSourceValueWarning(Exception):
    """
    Exception type that allow acteur insertion as a suggestion but add a warning
    """

    is_blocking = False


class BooleanValueWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class ActeurTypeCodeError(ImportSourceException, ImportSourceValueError):
    pass


class CodePostalWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class ActeurServiceCodesWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class ActionCodesWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class AdresseWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class IdentifiantExterneError(ImportSourceException, ImportSourceValueError):
    pass


class IdentifiantUniqueError(ImportSourceException, ImportSourceValueError):
    pass


class OpeningHoursWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class PublicAccueilliWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class RepriseWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class SirenWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class SiretWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class SousCategorieCodesError(ImportSourceException, ImportSourceValueError):
    pass


class UrlWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class EmailWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class TelephoneWarning(ImportSourceException, ImportSourceValueWarning):
    pass


class GeopointWarning(ImportSourceException, ImportSourceValueWarning):
    pass
