from django.urls import path

from .views import ColorsView

urlpatterns = [path("colors", ColorsView.as_view(), name="colors")]
