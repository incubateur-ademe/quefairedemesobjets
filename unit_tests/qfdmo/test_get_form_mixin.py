from django import forms
from django.http import QueryDict

from qfdmo.mixins import GetFormMixin


class SampleForm(GetFormMixin, forms.Form):
    """Test form using GetFormMixin"""

    name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    age = forms.IntegerField(required=False)


class TestGetFormMixin:
    def test_form_binds_data_when_prefixed_field_exists(self):
        """Test that form binds data when a prefixed field exists in data"""
        data = QueryDict("my_prefix-name=John&other_field=value")
        form = SampleForm(data=data, prefix="my_prefix")

        # Form should be bound because 'my_prefix-name' exists
        assert form.is_bound
        assert form.data is not None
        assert "my_prefix-name" in form.data

    def test_form_does_not_bind_when_no_prefixed_fields_exist(self):
        """Test that form doesn't bind data when no prefixed fields exist"""
        data = QueryDict("other_field=value&another_field=data")
        form = SampleForm(data=data, prefix="my_prefix")

        # Form should not be bound because no 'my_prefix-*' fields exist
        assert not form.is_bound

    def test_form_binds_with_multiple_prefixed_fields(self):
        """Test that form binds when multiple prefixed fields exist"""
        data = QueryDict("prefix-name=John&prefix-email=john@example.com&prefix-age=30")
        form = SampleForm(data=data, prefix="prefix")

        assert form.is_bound
        assert form.is_valid()
        assert form.cleaned_data["name"] == "John"
        assert form.cleaned_data["email"] == "john@example.com"
        assert form.cleaned_data["age"] == 30

    def test_form_without_prefix_binds_normally(self):
        """Test that form without prefix binds data normally"""
        data = QueryDict("name=Jane&email=jane@example.com")
        form = SampleForm(data=data)

        assert form.is_bound
        assert form.is_valid()
        assert form.cleaned_data["name"] == "Jane"

    def test_form_with_empty_data_dict(self):
        """Test that form handles empty data dict"""
        data = QueryDict("")
        form = SampleForm(data=data, prefix="prefix")

        # Empty data with prefix should result in unbound form
        assert not form.is_bound

    def test_form_with_none_data(self):
        """Test that form handles None data"""
        form = SampleForm(data=None, prefix="prefix")

        assert not form.is_bound

    def test_form_binds_with_partial_field_match(self):
        """Test that form binds even if only one prefixed field matches"""
        data = QueryDict("prefix-name=John&other_field=value")
        form = SampleForm(data=data, prefix="prefix")

        # Should bind because at least one prefixed field exists
        assert form.is_bound
        assert form.is_valid()
        assert form.cleaned_data["name"] == "John"
        assert form.cleaned_data["email"] == ""  # Empty but valid

    def test_form_with_similar_but_different_prefix(self):
        """Test that form doesn't bind with similar but different prefix"""
        data = QueryDict("my_prefix_other-name=John")
        form = SampleForm(data=data, prefix="my_prefix")

        # 'my_prefix_other-name' is not the same as 'my_prefix-name'
        assert not form.is_bound

    def test_prefix_assignment(self):
        """Test that prefix is correctly assigned to form"""
        form = SampleForm(data=QueryDict(""), prefix="test_prefix")

        assert form.prefix == "test_prefix"

    def test_add_prefix_functionality(self):
        """Test that add_prefix works correctly with mixin"""
        form = SampleForm(prefix="myform")

        assert form.add_prefix("name") == "myform-name"
        assert form.add_prefix("email") == "myform-email"

    def test_real_world_scenario_multiple_forms_same_page(self):
        """Test real-world scenario with multiple forms on the same page"""
        # Simulate a page with multiple forms, only one should bind
        data = QueryDict(
            "form1-name=Alice&form1-email=alice@example.com&unrelated_field=value"
        )

        form1 = SampleForm(data=data, prefix="form1")
        form2 = SampleForm(data=data, prefix="form2")
        form3 = SampleForm(data=data, prefix="form3")

        # Only form1 should bind
        assert form1.is_bound
        assert not form2.is_bound
        assert not form3.is_bound

        # form1 should have valid data
        assert form1.is_valid()
        assert form1.cleaned_data["name"] == "Alice"
