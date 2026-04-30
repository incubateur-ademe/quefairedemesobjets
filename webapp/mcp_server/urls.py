from django.urls import path

from . import server, views

urlpatterns = [
    path("mcp", server.mcp_endpoint, name="mcp_endpoint"),
    path("mcp/docs/<slug:slug>.md", views.doc_markdown, name="mcp_doc"),
    path("llms.txt", views.llms_txt, name="llms_txt"),
    path("llms-full.txt", views.llms_full_txt, name="llms_full_txt"),
]
