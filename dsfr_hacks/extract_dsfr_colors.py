import re

import requests

r = requests.get("http://localhost:8000/static/qfdmo.css")
css = r.text

# Étape 1 : Extraire uniquement le contenu de `:root { ... }`
root_block_pattern = r":root\s*\{([^}]*)\}"
root_content_match = re.search(root_block_pattern, css)
if root_content_match:
    root_content = root_content_match.group(1)
else:
    print("Aucune variable CSS n'a été trouvée")
    exit()

pattern = r"(--[a-zA-Z0-9-]+):\s*(#[0-9a-fA-F]{3,6});"
color_variables = re.findall(pattern, root_content)


js_content = "const colorVariables = {\n"
for var, color in color_variables:
    js_content += f"  '{var.replace('--', '')}': '{color}',\n"
js_content += "};\n\nexport default colorVariables;\n"

with open("dsfr_hacks/colors.js", "w") as js_file:
    js_file.write(js_content)

# Création du contenu du fichier colors.py
python_content = "DSFRColors = {\n"
for var, color in color_variables:
    # Remplace les tirets par des underscores pour une meilleure compatibilité en Python
    python_content += f"    '{var.replace('--', '')}': '{color}',\n"
python_content += "}\n"

with open("dsfr_hacks/colors.py", "w") as py_file:
    py_file.write(python_content)
