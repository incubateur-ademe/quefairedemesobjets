from pathlib import Path


def load_dag_doc_md(filename: str) -> str:
    module_file = Path(__file__).resolve()
    for ancestor in (module_file.parents[3], module_file.parents[2]):
        doc_path = ancestor / "docs/reference/data-platform" / filename
        if doc_path.is_file():
            return doc_path.read_text(encoding="utf-8")
    msg = f"DAG documentation not found: {filename}"
    raise FileNotFoundError(msg)
