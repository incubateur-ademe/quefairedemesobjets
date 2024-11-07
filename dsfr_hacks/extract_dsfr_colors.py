import re

import requests


def format_line(variable, value):
    return f"  '{variable.replace('--', '')}': '{value}',\n"


# Generate css variables dict
r = requests.get("http://localhost:8000/static/qfdmo.css")
css = r.text

root_pattern = r":root(?:\[[^\]]*\])?\s*{([^}]*)}"
root_blocks = re.findall(root_pattern, css, re.DOTALL)
css_variables = {}

for block in root_blocks:
    variables = re.findall(r"--([a-zA-Z0-9-_]+)\s*:\s*(#[^;]+);", block)

    for name, value in variables:
        if name not in css_variables:
            css_variables[name] = value.strip()

# THIS IS A HACK BECAUSE FORMULAIRE VERSION USES A BAD COLOR NAME
# TODO: write better documentation regarding this case.
css_variables["yellow-tournesol-sun-407-moon-922-active"] = "#cab300"

# Generate js file
js_content = "const colorVariables = {\n"
for variable, value in css_variables.items():
    js_content += format_line(variable, value)
js_content += "};\n\nexport default colorVariables;\n"

# Generate python file
python_content = "DSFRColors = {\n"
for variable, value in css_variables.items():
    # Remplace les tirets par des underscores pour une meilleure compatibilité en Python
    python_content += format_line(variable, value)
python_content += "}\n"


# Write files
with open("dsfr_hacks/colors.py", "w") as py_file:
    py_file.write(python_content)

with open("dsfr_hacks/colors.js", "w") as js_file:
    js_file.write(js_content)
