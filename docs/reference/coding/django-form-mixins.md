# Django Form Mixins

## CarteConfigFormMixin

A mixin that allows overriding form field choices and initial values based on `CarteConfig` model fields.

### Usage

```python
from qfdmo.mixins import CarteConfigFormMixin

class MyForm(CarteConfigFormMixin, forms.Form):
    # Map form fields to CarteConfig ManyToMany fields for choices override
    carte_config_choices_mapping = {
        'groupe_action': 'groupe_action',
        'label_qualite': 'label_qualite',
    }

    # Map form fields to CarteConfig fields for initial value override
    carte_config_initial_mapping = {
        'view': 'mode_affichage',
    }

    groupe_action = forms.ModelMultipleChoiceField(...)
    label_qualite = forms.ModelMultipleChoiceField(...)
    view = forms.ChoiceField(...)

# Apply overrides
form.apply_carte_config_overrides(carte_config)
```

### How It Works

**Choices Override**: Filters `ModelChoiceField`/`ModelMultipleChoiceField` querysets to only include items present in the corresponding CarteConfig ManyToMany field.

**Initial Override**: Sets field initial values from CarteConfig field values (only if non-None/non-empty).

### Examples

```python
# LegendeForm - filters available action groups
class LegendeForm(GetFormMixin, CarteConfigFormMixin, DsfrBaseForm):
    carte_config_choices_mapping = {"groupe_action": "groupe_action"}
    groupe_action = GroupeActionChoiceField(...)

# ViewModeForm - sets initial display mode
class ViewModeForm(GetFormMixin, CarteConfigFormMixin, DsfrBaseForm):
    carte_config_initial_mapping = {"view": "mode_affichage"}
    view = forms.ChoiceField(initial=CarteConfig.ModesAffichage.CARTE)
```

## GetFormMixin

A mixin that conditionally initializes form data based on whether matching prefixed fields exist in the request data.

### Usage

```python
from qfdmo.mixins import GetFormMixin

class MyForm(GetFormMixin, forms.Form):
    my_field = forms.CharField()

# With prefix
form = MyForm(data=request.GET, prefix="my_prefix")
# Form will only bind data if 'my_prefix-my_field' exists in request.GET
```

### How It Works

Checks if any field with the form's prefix exists in the provided data. If none exist, sets data to `None`, leaving the form unbound.

## AutoSubmitMixin

A mixin that automatically adds auto-submit data attributes to specified form fields.

### Usage

```python
from qfdmo.mixins import AutoSubmitMixin

class MyForm(AutoSubmitMixin, forms.Form):
    autosubmit_fields = ["field1", "field2"]
    autosubmit_action = "search-solution-form#submitForm"  # Optional, this is the default

    field1 = forms.CharField()
    field2 = forms.ChoiceField()

# With custom action
class CustomForm(AutoSubmitMixin, forms.Form):
    autosubmit_fields = ["my_field"]
    autosubmit_action = "my-controller#customAction"

    my_field = forms.CharField()
```

### How It Works

Adds `data-action` attribute to widgets of fields listed in `autosubmit_fields`, enabling automatic form submission on field change. The action value can be customized via the `autosubmit_action` attribute (defaults to `"search-solution-form#submitForm"`).

## Implementation

All mixins are located in `qfdmo/mixins/` with comprehensive unit tests in `unit_tests/qfdmo/test_*_mixin.py`.
