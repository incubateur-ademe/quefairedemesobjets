import mimetypes

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles import finders
from django.http import HttpResponse


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
