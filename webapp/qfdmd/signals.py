import logging

from core.notion import ContactFormData, create_new_row_in_notion_table
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from modelsearch.index import insert_or_update_object
from pydantic import ValidationError
from qfdmd.models import FormPageValidationSettings, ProduitPage
from sites_conformes.forms.models import FormPage
from wagtail.contrib.forms.models import FormSubmission
from wagtail.signals import page_published

# Warning : this could change if Sites Faciles creates their
# own form submission class.
# Using FormPage.get_submission_class would raise a warning
# as it could access the db before django apps are ready.
#
# So be aware of this if Notion integration breaks at some point.
# TODO: add a test that checks that FormPage().get_submission_class() == FormSubmission
submission_class = FormSubmission

logger = logging.getLogger(__name__)


@receiver(page_published, sender=ProduitPage)
def index_produit_page_search_term(sender, instance, **kwargs):
    """
    Re-index the ProduitPageSearchTerm when a ProduitPage is published.

    The search index is updated here (rather than relying solely on post_save)
    because Wagtail drafts call save() on the revision without publishing,
    and get_indexed_objects excludes terms whose page is not live.
    Triggering indexing on page_published ensures the term becomes searchable
    as soon as the page goes live.
    """
    try:
        search_term = instance.produit_page_search_term
    except instance.__class__.produit_page_search_term.RelatedObjectDoesNotExist:
        return
    insert_or_update_object(search_term)


@receiver(post_save, sender=submission_class)
def submit_sites_conformes_form(sender, instance, created, **kwargs):
    if created:
        settings_instance = FormPageValidationSettings.objects.first()
        if (
            not settings_instance
            or not settings_instance.form_page
            or instance.page_id != settings_instance.form_page_id
        ):
            return

        form_data = instance.get_data()
        fields_names = [field.clean_name for field in instance.page.get_form_fields()]
        data_dict = {
            "name": form_data.get(fields_names[0]),
            "email": form_data.get(fields_names[1]),
            "subject": form_data.get(fields_names[2]),
            "message": form_data.get(fields_names[3]),
        }
        try:
            validated_data = ContactFormData(**data_dict)
            create_new_row_in_notion_table(
                settings.NOTION.get("CONTACT_FORM_DATABASE_ID"), validated_data
            )
        except ValidationError as exception:
            # log or return the errors to user
            logger.error(exception.json())
            return


@receiver(post_save, sender=FormPage)
def validate_form_page_fields(sender, instance: FormPage, created, **kwargs):
    """
    Validate that the FormPage has exactly 4 fields when it matches
    the configured page in FormPageValidationSettings.

    These 4 fields are used in Notion bridge in core/notion.py and
    in the signal above.
    """
    settings_instance = FormPageValidationSettings.objects.first()
    if not settings_instance or not settings_instance.form_page:
        return

    # Check if this is the configured form page
    if instance.pk != settings_instance.form_page.pk:
        return

    # Get the form fields count
    form_fields = instance.get_form_fields()
    field_count = len(form_fields)

    if field_count != 4:
        error_message = (
            f"The form page '{instance.title}' must have exactly "
            f"4 fields, but has {field_count}. This error is "
            "silently logged but should be addressed quickly."
        )
        logger.error(error_message)
