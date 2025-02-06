"""Script pour mettre à jour les toctree des README.md:
    - Récupère les sous-dossiers directs de docs/
    - Pour chaque sous-dossier:
        - Récupère les fichiers .md
        - Génère un toctree
        - Met à jour le README.md du sous-dossier avec le toctree
 """

import os
import re
from pathlib import Path

from rich import print
from rich.prompt import Confirm


def folders_get(base_path):
    return [f for f in base_path.iterdir() if f.is_dir()]


def files_md_get(subfolder):
    md_files = []
    for file in subfolder.rglob("*.md"):
        if file.name != "README.md":
            md_files.append(file.relative_to(subfolder))
    return md_files


def toctree_generate(md_files):
    if not md_files:
        return ""

    toc = ["```{toctree}\n:hidden:\n\n"]
    toc.extend(f"{file}\n" for file in md_files)
    toc.append("```\n")
    return "".join(toc)


def readme_update_toc(subfolder, toctree):
    readme_path = subfolder / "README.md"

    if not readme_path.is_file():
        return

    content = readme_path.read_text(encoding="utf-8")

    toctree_pattern = r"```{toctree}.*?```"

    if re.search(toctree_pattern, content, re.DOTALL):
        content = re.sub(toctree_pattern, toctree, content, flags=re.DOTALL)
    else:
        title_pattern = r"(^# .*\n)(\n*?)"
        match = re.search(title_pattern, content)

        if match:
            insert_pos = match.end()
            content = (
                content[:insert_pos] + "\n" + toctree + "\n" + content[insert_pos:]
            )

    print(f"Mise à jour de {readme_path=} avec:\n")
    print(toctree)

    if Confirm.ask("Continuer?"):
        readme_path.write_text(content, encoding="utf-8")


def main():
    base_path = Path(__file__).resolve().parent
    subfolders = folders_get(base_path)

    for subfolder in subfolders:
        folder_name = os.path.basename(subfolder)
        md_files = files_md_get(subfolder)
        toctree = toctree_generate(md_files)

        if toctree:
            print(f"toctree pour {folder_name=}\n")
            print(toctree)

            readme_update_toc(subfolder, toctree)


if __name__ == "__main__":
    main()
