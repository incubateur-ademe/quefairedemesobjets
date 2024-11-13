import requests

r = requests.get("http://localhost:8000/api/qfdmo/actions")
actions = r.json()
colors = [action["background"] for action in actions]

r = requests.get("http://localhost:8000/api/qfdmo/actions/groupes")
groupe_actions = r.json()
colors.extend(
    [
        *[action["background"] for action in groupe_actions],
        *[action["border"] for action in groupe_actions],
    ]
)

# Generate js file
js_content = "const usedColors = [\n"
for color in colors:
    js_content += f'"{color}",'
js_content += "];\n\nexport default usedColors;\n"

# Write files
with open("dsfr_hacks/used_colors.js", "w") as js_file:
    js_file.write(js_content)
