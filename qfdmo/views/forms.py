from django.conf import settings
from django.http import HttpResponseRedirect


def address_suggestion_form(request):
    return HttpResponseRedirect(settings.ADDRESS_SUGGESTION_FORM)


def contact_form(request):
    return HttpResponseRedirect(settings.CONTACT_FORM)


def update_suggestion_form(request):
    return HttpResponseRedirect(settings.UPDATE_SUGGESTION_FORM)


def feedback_form(request):
    return HttpResponseRedirect(settings.FEEDBACK_FORM)
