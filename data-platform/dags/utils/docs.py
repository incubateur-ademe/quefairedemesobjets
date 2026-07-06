from pathlib import Path


def load_dag_doc_md(filename: str) -> str:
    module_file = Path(__file__).resolve()
    base_path = module_file.parents[3]
    doc_path = base_path / "docs/reference/data-platform" / filename
    if not doc_path.is_file():
        msg = f"DAG documentation not found: {filename}"
        raise FileNotFoundError(msg)
    return doc_path.read_text(encoding="utf-8")
