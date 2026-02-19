class TurboFrameConfigurationError(Exception):
    pass


class CarteConfigFormMappingError(Exception):
    """Raised when a form's carte_config mapping references non-existent
    CarteConfig fields."""

    pass


class CarteConfigChoicesMappingError(CarteConfigFormMappingError):
    """Raised when carte_config_choices_mapping references a field that
    doesn't exist in CarteConfig."""

    pass


class CarteConfigInitialMappingError(CarteConfigFormMappingError):
    """Raised when carte_config_initial_mapping references a field that
    doesn't exist in CarteConfig."""

    pass
