import pytest

from mcp_server import docs as docs_module


@pytest.mark.django_db
class TestLlmsTxt:
    def test_returns_markdown(self, client):
        response = client.get("/llms.txt")
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/markdown")

    def test_contains_intro_and_section_headings(self, client):
        body = client.get("/llms.txt").content.decode("utf-8")
        assert "Que Faire De Mes Objets et Déchets" in body
        assert "## Documentation principale" in body
        assert "## Référence" in body
        assert "## Exemples" in body

    def test_links_to_each_doc(self, client):
        body = client.get("/llms.txt").content.decode("utf-8")
        for doc in docs_module.DOCS:
            assert f"/mcp/docs/{doc.slug}.md" in body, doc.slug
            assert doc.title in body, doc.slug


@pytest.mark.django_db
class TestLlmsFullTxt:
    def test_returns_markdown_with_all_docs(self, client):
        response = client.get("/llms-full.txt")
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/markdown")
        body = response.content.decode("utf-8")
        for doc in docs_module.DOCS:
            assert f"<!-- file: {doc.filename} -->" in body, doc.slug


@pytest.mark.django_db
class TestDocMarkdown:
    @pytest.mark.parametrize("doc", list(docs_module.DOCS), ids=lambda d: d.slug)
    def test_each_doc_is_served(self, client, doc):
        response = client.get(f"/mcp/docs/{doc.slug}.md")
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/markdown")
        assert response.content.decode("utf-8") == docs_module.read(doc)

    def test_unknown_slug_returns_404(self, client):
        response = client.get("/mcp/docs/does-not-exist.md")
        assert response.status_code == 404

    def test_path_traversal_is_rejected(self, client):
        response = client.get("/mcp/docs/..%2F..%2Fsettings.md")
        assert response.status_code == 404
