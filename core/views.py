import mimetypes

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.views.decorators.cache import cache_control


@cache_control(max_age=31536000)
def robots_txt(request):
    text_content = render_to_string("robots.txt", request=request)
    return HttpResponse(text_content, content_type="text/plain")


def direct_access(request):
    from qfdmd.views import HomeView as Assistant  # avoid circular dependency

    get_params = request.GET.copy()

    # FIXME: check if view is assistant
    if request.META.get("HTTP_HOST") in settings.ASSISTANT["HOSTS"]:
        return Assistant.as_view()(request)

    # FIXME: check if view is carte
    if "carte" in request.GET:
        # Order matters, this should be before iframe because iframe and carte
        # parameters can coexist
        del get_params["carte"]
        try:
            del get_params["iframe"]
        except KeyError:
            pass
        params = get_params.urlencode()
        parts = [reverse("qfdmo:carte"), "?" if params else "", params]
        return redirect("".join(parts))

    # FIXME: check if view is carte
    if "iframe" in request.GET:
        del get_params["iframe"]
        params = get_params.urlencode()
        parts = [reverse("qfdmo:formulaire"), "?" if params else "", params]
        return redirect("".join(parts))

    return redirect(f"{settings.CMS['BASE_URL']}/lacarte", permanent=False)


def static_file_content_from(path):
    file_path = finders.find(path)

    if not file_path:
        return HttpResponse("File not found", status=404)

    content_type, _ = mimetypes.guess_type(file_path)
    # If the MIME type cannot be guessed (e.g., unknown file extension),
    # we default to application/octet-stream, which is a generic binary type.
    content_type = content_type or "application/octet-stream"

    with open(file_path, "r") as file:
        file_content = file.read()
        return HttpResponse(file_content, content_type=content_type)


class IsStaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
