import json
from html import escape
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import FormView

from qfdmo.forms import AdvancedConfiguratorForm, ConfiguratorForm

BAN_API_URL = "https://api-adresse.data.gouv.fr/search/?q={}"


class ConfiguratorView(FormView):
    form_class = ConfiguratorForm
    template_name = "qfdmo/iframe_configurator/base.html"

    def form_valid(self, form) -> HttpResponse:
        return render(
            self.request,
            self.template_name,
            self.get_context_data(
                form=form, iframe_script=self._compile_script_tag(form.cleaned_data)
            ),  # Inherited from django.views.generic.edit.FormMixin.form_invalid
        )

    @property
    def iframe_url(self):
        return f"{self.request.scheme}://{self.request.get_host()}/static/carte.js"

    def _compile_script_tag(self, attributes):
        iframe_script = f"<script src='{ self.iframe_url }'"
        for key, value in attributes.items():
            try:
                # Some values need to be formatted
                value = value.as_codes()
            except AttributeError:
                pass

            if value:
                iframe_script += f" data-{key}='{str(value)}'"
        iframe_script += "></script>"
        return iframe_script

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context


class AdvancedConfiguratorView(LoginRequiredMixin, FormView):
    form_class = AdvancedConfiguratorForm
    template_name = "qfdmo/iframe_configurator/advanced.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["limit"] = self.request.GET.get("limit")
        initial["address_placeholder"] = self.request.GET.get("address_placeholder")
        initial["iframe_mode"] = self.request.GET.get("iframe_mode")
        initial["direction"] = self.request.GET.get("direction")
        initial["first_dir"] = self.request.GET.get("first_dir")
        initial["action_displayed"] = self.request.GET.getlist("action_displayed")
        initial["action_list"] = self.request.GET.getlist("action_list")
        initial["max_width"] = self.request.GET.get("max_width")
        initial["height"] = self.request.GET.get("height")
        initial["iframe_attributes"] = self.request.GET.get("iframe_attributes")
        initial["bounding_box"] = self.request.GET.get("bounding_box")
        return initial

    def get_context_data(self, **kwargs):
        # TODO : clean up input to avoid security issues
        iframe_mode = self.request.GET.get("iframe_mode")

        iframe_host = (
            "http"
            + ("s" if self.request.is_secure() else "")
            + "://"
            + self.request.get_host()
        )

        iframe_url = None
        if iframe_mode == "carte":
            iframe_url = iframe_host + "/static/carte.js"
        if iframe_mode == "form":
            iframe_url = iframe_host + "/static/iframe.js"

        attributes = {}
        if direction := self.request.GET.get("direction"):
            if direction != "no_dir":
                attributes["direction"] = escape(direction)
        if first_dir := self.request.GET.get("first_dir"):
            if first_dir != "first_no_dir":
                attributes["first_dir"] = escape(first_dir.replace("first_", ""))
        if action_list := self.request.GET.getlist("action_list"):
            attributes["action_list"] = escape("|".join(action_list))
        if action_displayed := self.request.GET.getlist("action_displayed"):
            attributes["action_displayed"] = escape("|".join(action_displayed))
        if max_width := self.request.GET.get("max_width"):
            attributes["max_width"] = escape(max_width)
        if height := self.request.GET.get("height"):
            attributes["height"] = height
        if limit := self.request.GET.get("limit"):
            attributes["limit"] = limit
        if address_placeholder := self.request.GET.get("address_placeholder"):
            attributes["address_placeholder"] = address_placeholder
        if iframe_attributes := self.request.GET.get("iframe_attributes"):
            try:
                attributes["iframe_attributes"] = json.dumps(
                    json.loads(iframe_attributes.replace("\r\n", "").replace("\n", ""))
                )
            except json.JSONDecodeError:
                attributes["iframe_attributes"] = ""
        if bounding_box := self.request.GET.get("bounding_box"):
            try:
                attributes["bounding_box"] = json.dumps(
                    json.loads(bounding_box.replace("\r\n", "").replace("\n", ""))
                )
            except json.JSONDecodeError:
                attributes["bounding_box"] = ""

        if iframe_url:
            kwargs["iframe_script"] = f"<script src='{ iframe_url }'"
            for key, value in attributes.items():
                kwargs["iframe_script"] += f" data-{key}='{value}'"
            kwargs["iframe_script"] += "></script>"

        return super().get_context_data(**kwargs)
