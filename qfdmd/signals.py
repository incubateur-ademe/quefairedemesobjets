import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from pydantic import ValidationError
from wagtail.contrib.forms.models import FormSubmission

from core.notion import ContactFormData, create_new_row_in_notion_table

# Warning : this could change if Sites Faciles creates their
# own form submission class.
# Using FormPage.get_submission_class would raise a warning
# as it could access the db before django apps are ready.
#
# So be aware of this if Notion integration breaks at some point.
# TODO: add a test that checks that FormPage().get_submission_class() == FormSubmission
submission_class = FormSubmission

logger = logging.getLogger(__name__)


@receiver(post_save, sender=submission_class)
def submit_sites_faciles_form(sender, instance, created, **kwargs):
    if created:
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
