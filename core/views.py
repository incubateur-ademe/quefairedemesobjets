from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles import finders
from django.http import HttpResponse


def static_file_content_from(path):
    file_path = finders.find(path)

    with open(file_path, "r") as file:
        file_content = file.read()
        return HttpResponse(file_content, content_type="application/javascript")


class IsStaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
