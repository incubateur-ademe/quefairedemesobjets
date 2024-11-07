import re

import requests

LEGACY_MAPPING_FROM_TAILWIND = {
    "beige-gris-galet": "#AEA397",
    "blue-cumulus-sun-368-active": "#7996e6",
    "blue-cumulus-sun-368-hover": "#5982e0",
    "blue-cumulus-sun-368": "#3558A2",
    "blue-cumulus": "#417DC4",
    "blue-ecume-850-active": "#6b93f6",
    "blue-ecume-850-hover": "#8ba7f8",
    "blue-ecume-850": "#bfccfb",
    "blue-ecume": "#465F9D",
    "blue-france-850-hover": "#a1a1f8",
    "blue-france-850": "#cacafb",
    "blue-france-925-active": "#adadf9",
    "blue-france-925-hover": "#c1c1fb",
    "blue-france-925": "#e3e3fd",
    "blue-france-950-hover": "#cecefc",
    "blue-france-950": "#ececfe",
    "blue-france-975-hover": "#dcdcfc",
    "blue-france-975": "#f5f5fe",
    "blue-france-main-525-active": "#aeaef9",
    "blue-france-main-525-hover": "#9898f8",
    "blue-france-main-525": "#6a6af4",
    "blue-france-sun-113": "#000091",
    "blue-france": "#2323ff",
    "brown-cafe-creme-main-782-active": "#8b7954",
    "brown-cafe-creme-main-782-hover": "#a38e63",
    "brown-cafe-creme-main-782": "#D1B781",
    "brown-cafe-creme": "#D1B781",
    "brown-caramel": "#C08C65",
    "brown-opera": "#BD987A",
    "green-archipel": "#009099",
    "green-bourgeon-850-active": "#679e3b",
    "green-bourgeon-850-hover": "#77b645",
    "green-bourgeon-850": "#95e257",
    "green-bourgeon": "#68A532",
    "green-emeraude": "#00A95F",
    "green-menthe-850-active": "#4f9d91",
    "green-menthe-850-hover": "#5bb5a7",
    "green-menthe-850": "#73e0cf",
    "green-menthe-main-548-active": "#00e2cb",
    "green-menthe-main-548-hover": "#00c7b3",
    "green-menthe-main-548": "#009081",
    "green-menthe-sun-373-active": "#62a9a2",
    "green-menthe-sun-373-hover": "#53918c",
    "green-menthe-sun-373": "#37635f",
    "green-menthe": "#009081",
    "green-tilleul-verveine": "#B7A73F",
    "grey-50": "#161616",
    "grey-200": "#3a3a3a",
    "grey-425": "#666666",
    "grey-850": "#cecece",
    "grey-900": "#dddddd",
    "grey-925": "#e5e5e5",
    "grey-950": "#eeeeee",
    "grey-975": "#f6f6f6",
    "info-425": "#0063CB",
    "light-gray": "#e5e5e5",
    "orange-terre-battue-main-645-active": "#f4bfb1",
    "orange-terre-battue-main-645-hover": "#f1a892",
    "orange-terre-battue-main-645": "#E4794A",
    "orange-terre-battue": "#E4794A",
    "pink-macaron": "#E18B76",
    "pink-tuile-850-active": "#fa7659",
    "pink-tuile-850-hover": "#fb907d",
    "pink-tuile-850": "#fcbfb7",
    "pink-tuile": "#CE614A",
    "purple-glycine-main-494-active": "#db9cd6",
    "purple-glycine-main-494-hover": "#d282cd",
    "purple-glycine-main-494": "#A558A0",
    "purple-glycine": "#A558A0",
    "red-500": "#EB4444",
    "yellow-moutarde-850-active": "#b18a26",
    "yellow-moutarde-850-hover": "#cb9f2d",
    "yellow-moutarde-850": "#fcc63a",
    "yellow-moutarde": "#C3992A",
    "yellow-tournesol": "#cab300",
}


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


# Keep support for colors previously defined manually in tailwind.config.js
# These should be removed later in order to only used colors names coming from
# the DSFR
css_variables.update(**LEGACY_MAPPING_FROM_TAILWIND)

# THIS IS A HACK BECAUSE THE FORMULAIRE VIEW USES A BAD COLOR NAME
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
