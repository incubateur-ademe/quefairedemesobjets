from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from sites_faciles.forms.models import FormPage

from core.notion import create_new_row_in_notion_table

submission_class = FormPage().get_submission_class()


@receiver(post_save, sender=submission_class)
def submit_sites_faciles_form(sender, instance, created, **kwargs):
    if created:
        form_data = instance.get_data()
        submitted_subject = form_data.get("subject")
        form_data["subject"] = dict(
            FormPage().get_form_class().fields["subject"].choices
        )[submitted_subject]
        create_new_row_in_notion_table(
            settings.NOTION.get("CONTACT_FORM_DATABASE_ID"), form_data
        )
