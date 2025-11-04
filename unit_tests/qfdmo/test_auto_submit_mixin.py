from django import forms

from qfdmo.mixins import AutoSubmitMixin


class SampleAutoSubmitForm(AutoSubmitMixin, forms.Form):
    """Test form with auto-submit fields"""

    autosubmit_fields = ["field1", "field2"]

    field1 = forms.CharField(required=False)
    field2 = forms.ChoiceField(
        choices=[("a", "A"), ("b", "B")],
        required=False,
    )
    field3 = forms.EmailField(required=False)  # Not in autosubmit_fields


class TestAutoSubmitMixin:
    def test_autosubmit_fields_have_data_action_attribute(self):
        """Test that fields in autosubmit_fields have the data-action attribute"""
        form = SampleAutoSubmitForm()

        # Fields in autosubmit_fields should have the data-action attribute
        assert (
            form.fields["field1"].widget.attrs.get("data-action")
            == "search-solution-form#submitForm"
        )
        assert (
            form.fields["field2"].widget.attrs.get("data-action")
            == "search-solution-form#submitForm"
        )

    def test_non_autosubmit_fields_dont_have_attribute(self):
        """Test that fields not in autosubmit_fields don't have the attribute"""
        form = SampleAutoSubmitForm()

        # field3 is not in autosubmit_fields
        assert "data-action" not in form.fields["field3"].widget.attrs

    def test_empty_autosubmit_fields_list(self):
        """Test form with empty autosubmit_fields list"""

        class NoAutoSubmitForm(AutoSubmitMixin, forms.Form):
            autosubmit_fields = []

            field1 = forms.CharField(required=False)
            field2 = forms.CharField(required=False)

        form = NoAutoSubmitForm()

        # No fields should have the data-action attribute
        assert "data-action" not in form.fields["field1"].widget.attrs
        assert "data-action" not in form.fields["field2"].widget.attrs

    def test_nonexistent_field_in_autosubmit_list(self):
        """Test that nonexistent fields in autosubmit_fields are ignored"""

        class FormWithInvalidField(AutoSubmitMixin, forms.Form):
            autosubmit_fields = ["field1", "nonexistent_field"]

            field1 = forms.CharField(required=False)

        # Should not raise an error
        form = FormWithInvalidField()

        # field1 should still have the attribute
        assert (
            form.fields["field1"].widget.attrs.get("data-action")
            == "search-solution-form#submitForm"
        )

    def test_widget_with_existing_attributes(self):
        """Test that data-action is added even if widget has existing attributes"""

        class FormWithWidgetAttrs(AutoSubmitMixin, forms.Form):
            autosubmit_fields = ["field1"]

            field1 = forms.CharField(
                widget=forms.TextInput(attrs={"class": "custom-class", "id": "my-id"}),
                required=False,
            )

        form = FormWithWidgetAttrs()

        # Should preserve existing attributes and add data-action
        assert form.fields["field1"].widget.attrs.get("class") == "custom-class"
        assert form.fields["field1"].widget.attrs.get("id") == "my-id"
        assert (
            form.fields["field1"].widget.attrs.get("data-action")
            == "search-solution-form#submitForm"
        )

    def test_multiple_field_types(self):
        """Test that autosubmit works with various field types"""

        class MultiFieldForm(AutoSubmitMixin, forms.Form):
            autosubmit_fields = [
                "text_field",
                "choice_field",
                "checkbox_field",
                "select_field",
            ]

            text_field = forms.CharField(required=False)
            choice_field = forms.ChoiceField(
                choices=[("1", "One"), ("2", "Two")], required=False
            )
            checkbox_field = forms.BooleanField(required=False)
            select_field = forms.MultipleChoiceField(
                choices=[("a", "A"), ("b", "B")], required=False
            )

        form = MultiFieldForm()

        # All fields should have the data-action attribute
        for field_name in form.autosubmit_fields:
            assert (
                form.fields[field_name].widget.attrs.get("data-action")
                == "search-solution-form#submitForm"
            ), f"Field {field_name} should have data-action attribute"

    def test_mixin_with_no_autosubmit_fields_attribute(self):
        """Test that mixin works even if autosubmit_fields is not defined"""

        class FormWithoutAutoSubmitAttr(AutoSubmitMixin, forms.Form):
            # No autosubmit_fields defined
            field1 = forms.CharField(required=False)

        # Should not raise an error
        form = FormWithoutAutoSubmitAttr()

        # No fields should have the attribute since autosubmit_fields defaults to []
        assert "data-action" not in form.fields["field1"].widget.attrs

    def test_form_inheritance(self):
        """Test that autosubmit works with form inheritance"""

        class BaseForm(AutoSubmitMixin, forms.Form):
            autosubmit_fields = ["field1"]
            field1 = forms.CharField(required=False)

        class ExtendedForm(BaseForm):
            field2 = forms.CharField(required=False)

        form = ExtendedForm()

        # field1 from base should have the attribute
        assert (
            form.fields["field1"].widget.attrs.get("data-action")
            == "search-solution-form#submitForm"
        )
        # field2 should not (not in autosubmit_fields)
        assert "data-action" not in form.fields["field2"].widget.attrs

    def test_overriding_autosubmit_fields_in_subclass(self):
        """Test that subclass can override autosubmit_fields"""

        class BaseForm(AutoSubmitMixin, forms.Form):
            autosubmit_fields = ["field1"]
            field1 = forms.CharField(required=False)
            field2 = forms.CharField(required=False)

        class ExtendedForm(BaseForm):
            autosubmit_fields = ["field2"]  # Override parent's list

        form = ExtendedForm()

        # field2 should have the attribute (in subclass list)
        assert (
            form.fields["field2"].widget.attrs.get("data-action")
            == "search-solution-form#submitForm"
        )
        # field1 should not (not in subclass list)
        assert "data-action" not in form.fields["field1"].widget.attrs

    def test_custom_autosubmit_action(self):
        """Test that autosubmit_action can be customized"""

        class CustomActionForm(AutoSubmitMixin, forms.Form):
            autosubmit_fields = ["field1", "field2"]
            autosubmit_action = "my-custom-controller#customAction"

            field1 = forms.CharField(required=False)
            field2 = forms.CharField(required=False)

        form = CustomActionForm()

        # Fields should have the custom action
        assert (
            form.fields["field1"].widget.attrs.get("data-action")
            == "my-custom-controller#customAction"
        )
        assert (
            form.fields["field2"].widget.attrs.get("data-action")
            == "my-custom-controller#customAction"
        )

    def test_default_autosubmit_action_when_not_specified(self):
        """Test that default action is used when autosubmit_action is not specified"""

        class DefaultActionForm(AutoSubmitMixin, forms.Form):
            autosubmit_fields = ["field1"]
            # No autosubmit_action specified

            field1 = forms.CharField(required=False)

        form = DefaultActionForm()

        # Should use the default action
        assert (
            form.fields["field1"].widget.attrs.get("data-action")
            == "search-solution-form#submitForm"
        )

    def test_overriding_autosubmit_action_in_subclass(self):
        """Test that subclass can override autosubmit_action"""

        class BaseForm(AutoSubmitMixin, forms.Form):
            autosubmit_fields = ["field1"]
            autosubmit_action = "base-controller#baseAction"
            field1 = forms.CharField(required=False)

        class ExtendedForm(BaseForm):
            autosubmit_action = "extended-controller#extendedAction"

        form = ExtendedForm()

        # Should use the subclass action
        assert (
            form.fields["field1"].widget.attrs.get("data-action")
            == "extended-controller#extendedAction"
        )
