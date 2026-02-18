from django.forms import ModelChoiceField, ModelMultipleChoiceField

from core.exceptions import (
    CarteConfigChoicesMappingError,
    CarteConfigInitialMappingError,
)


class CarteConfigFormMixin:
    from qfdmo.models import CarteConfig

    """A mixin that allows overriding form field choices and
    initial values based on CarteConfig model fields."""

    # Mapping between form field names and CarteConfig ManyToMany
    # field names for choices override.
    carte_config_choices_mapping: dict[str, str] = {}

    # Mapping between form field names and CarteConfig field names
    # for initial values override.
    carte_config_initial_mapping: dict[str, str] = {}

    def __init__(
        self,
        *args,
        carte_config: CarteConfig | None = None,
        legacy_form=None,
        **kwargs,
    ):
        """Initialize the form and apply carte_config overrides if provided.

        Args:
            carte_config: Optional CarteConfig instance to apply overrides from.
            *args, **kwargs: Standard form initialization arguments.

        Raises:
            CarteConfigChoicesMappingError: If carte_config_choices_mapping references
                a non-existent CarteConfig field.
            CarteConfigInitialMappingError: If carte_config_initial_mapping references
                a non-existent CarteConfig field.
        """
        # Validate mappings on form class instantiation
        self._validate_carte_config_mappings()

        self.carte_config = carte_config

        super().__init__(*args, **kwargs)

        # Override choices and field initial values after form is initialized
        if self.carte_config:
            self._override_choices_from_carte_config()
            self._override_field_initial_from_carte_config()
            self._add_carte_config_on_all_fields_widget()

        # Apply legacy querystring overrides if the form implements the method
        # Querystring parameters should override carte_config
        if hasattr(self, "_apply_legacy_querystring_overrides"):
            self._apply_legacy_querystring_overrides(legacy_form)

    def _add_carte_config_on_all_fields_widget(self):
        for field in self.fields.values():
            field.widget.carte_config = self.carte_config

    def _restrict_field_choices_to_queryset(
        self,
        form_field_name: str,
        source_queryset,
    ) -> None:
        """Restrict a form field's choices to only include IDs from a source queryset.

        This is a reusable helper that restricts a ModelChoiceField or
        ModelMultipleChoiceField's queryset based on IDs present in another queryset.
        """
        # Only proceed if source queryset has values
        if not source_queryset.exists():
            return

        # Check if the form field exists
        if form_field_name not in self.fields:
            return

        # Check if it's a model choice field
        if not isinstance(
            self.fields[form_field_name],
            (ModelChoiceField, ModelMultipleChoiceField),
        ):
            return

        # Filter the form field's queryset to only include IDs from source
        self.fields[form_field_name].queryset = self.fields[
            form_field_name
        ].queryset.filter(id__in=source_queryset.values_list("id", flat=True))

    def _override_field_initial_from_carte_config(self) -> None:
        """Override field.initial values after form initialization.

        This is needed because Django doesn't override field-level initial values
        with form-level initial values when the field has initial= defined.

        Args:
            carte_config: CarteConfig instance to get values from.
        """
        if not self.carte_config_initial_mapping:
            return

        # Get all ManyToMany field names from CarteConfig
        many_to_many_fields_names = [
            field.name for field in self.carte_config.__class__._meta.many_to_many
        ]

        for (
            form_field_name,
            config_field_name,
        ) in self.carte_config_initial_mapping.items():
            # Check if the form field exists
            if form_field_name not in self.fields:
                continue

            # Check if the config field exists
            if not hasattr(self.carte_config, config_field_name):
                continue

            # Get the value from the config
            config_value = getattr(self.carte_config, config_field_name)

            # Handle ManyToMany fields specially
            if config_field_name in many_to_many_fields_names:
                # For ManyToMany fields, check if there are any related objects
                if config_value.exists():
                    # Set the initial value to the queryset or list of objects
                    self.fields[form_field_name].initial = config_value.all()
            # Only override if there's a meaningful value
            elif config_value is not None and config_value != "":
                # Set the initial value on the field instance
                self.fields[form_field_name].initial = config_value

    def _override_choices_from_carte_config(self) -> None:
        """Override queryset choices for ModelChoiceField/ModelMultipleChoiceField
        based on ManyToMany fields in CarteConfig."""
        # TODO: check in __init__ that mapping uses only many to many fields
        # from carteconfig
        # if not : raise an improperlyconfigurederror
        if not self.carte_config_choices_mapping:
            return

        # Get all ModelChoiceField field names from form
        model_choice_fields_names = [
            name
            for name, field in self.fields.items()
            if isinstance(field, (ModelChoiceField, ModelMultipleChoiceField))
        ]

        # Find fields that are mapped and eligible for override
        eligible_form_fields = set(self.carte_config_choices_mapping.keys()) & set(
            model_choice_fields_names
        )

        for form_field_name in eligible_form_fields:
            config_field_name = self.carte_config_choices_mapping[form_field_name]

            # Get the related manager for the config field
            config_field_value = getattr(self.carte_config, config_field_name)

            # Use the helper to restrict the field's choices
            self._restrict_field_choices_to_queryset(
                form_field_name, config_field_value.all()
            )

    def _validate_carte_config_mappings(self) -> None:
        """Validate that all mappings reference existing CarteConfig fields."""
        from qfdmo.models import CarteConfig

        # Get all field names from CarteConfig
        carte_config_fields = {field.name for field in CarteConfig._meta.get_fields()}

        # Validate choices mapping
        if self.carte_config_choices_mapping:
            invalid_choices_fields = (
                set(self.carte_config_choices_mapping.values()) - carte_config_fields
            )

            if invalid_choices_fields:
                raise CarteConfigChoicesMappingError(
                    f"Form {self.__class__.__name__} has invalid "
                    f"carte_config_choices_mapping: fields {invalid_choices_fields} "
                    f"do not exist in CarteConfig. "
                    f"Available fields: {sorted(carte_config_fields)}"
                )

        # Validate initial mapping
        if self.carte_config_initial_mapping:
            invalid_initial_fields = (
                set(self.carte_config_initial_mapping.values()) - carte_config_fields
            )

            if invalid_initial_fields:
                raise CarteConfigInitialMappingError(
                    f"Form {self.__class__.__name__} has invalid "
                    f"carte_config_initial_mapping: fields {invalid_initial_fields} "
                    f"do not exist in CarteConfig. "
                    f"Available fields: {sorted(carte_config_fields)}"
                )
