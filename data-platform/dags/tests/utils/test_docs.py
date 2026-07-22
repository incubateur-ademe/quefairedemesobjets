import pytest

from utils.docs import load_dag_doc_md


class TestLoadDagDocMd:
    def test_load_existing_doc(self):
        content = load_dag_doc_md("enrich-siret-siren.md")
        assert content.startswith("# Enrich — Acteurs SIRET & SIREN")
        assert "enrich_siret_siren" in content

    def test_load_lien_succession_doc(self):
        content = load_dag_doc_md("enrich-siret-siren-lien-succession.md")
        assert content.startswith("# Enrich — Acteurs SIRET & SIREN (lien succession)")
        assert "enrich_siret_siren_lien_succession" in content

    def test_raises_when_doc_not_found(self):
        with pytest.raises(FileNotFoundError, match="missing-doc.md"):
            load_dag_doc_md("missing-doc.md")
