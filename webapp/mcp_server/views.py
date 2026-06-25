from __future__ import annotations

from django.http import Http404, HttpRequest, HttpResponse
from django.views.decorators.http import require_GET

from . import docs as docs_module

MARKDOWN_CT = "text/markdown; charset=utf-8"

LLMS_INTRO = """\
# Que Faire De Mes Objets et Déchets — guide pour LLM

> Jeu de données public français recensant ~ 380 000 acteurs de l'économie
> circulaire (réparation, seconde main, dons, location, points de collecte,
> tri). Ce fichier explique à un LLM comment interroger l'API ADEME data-fair
> pour répondre à des questions du type « où réparer mon téléphone à Paris ? »
> ou « où jeter un pot de peinture à moitié plein ? ».
>
> Les ressources et le prompt équivalents sont aussi exposés via le serveur
> MCP de ce site, à l'URL `/mcp` (transport HTTP, JSON-RPC).

"""


def _doc_url(request: HttpRequest, doc: docs_module.Doc) -> str:
    return request.build_absolute_uri(f"/mcp/docs/{doc.slug}.md")


def _llms_index(request: HttpRequest) -> str:
    sections = {
        "Documentation principale": ["about", "workflow", "geocoding", "search-api"],
        "Référence": ["actions", "sous-categories", "sources"],
        "Exemples": ["examples"],
    }
    parts: list[str] = [LLMS_INTRO]
    for heading, slugs in sections.items():
        parts.append(f"## {heading}\n")
        for slug in slugs:
            doc = docs_module.DOCS_BY_SLUG[slug]
            parts.append(
                f"- [{doc.title}]({_doc_url(request, doc)}): {doc.description}"
            )
        parts.append("")
    return "\n".join(parts) + "\n"


@require_GET
def llms_txt(request: HttpRequest) -> HttpResponse:
    return HttpResponse(_llms_index(request), content_type=MARKDOWN_CT)


@require_GET
def llms_full_txt(request: HttpRequest) -> HttpResponse:
    parts: list[str] = [_llms_index(request), "---\n"]
    for doc in docs_module.DOCS:
        parts.append(f"\n<!-- file: {doc.filename} -->\n")
        parts.append(docs_module.read(doc))
    return HttpResponse("\n".join(parts), content_type=MARKDOWN_CT)


@require_GET
def doc_markdown(request: HttpRequest, slug: str) -> HttpResponse:
    doc = docs_module.DOCS_BY_SLUG.get(slug)
    if doc is None:
        raise Http404(f"Unknown doc slug: {slug}")
    return HttpResponse(docs_module.read(doc), content_type=MARKDOWN_CT)
