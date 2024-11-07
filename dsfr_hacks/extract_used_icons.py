import requests

r = requests.get("http://localhost:8000/api/qfdmo/actions")
actions = r.json()
icons = [action["icon"] for action in actions]

r = requests.get("http://localhost:8000/api/qfdmo/actions/groupes")
groupe_actions = r.json()
icons.extend([action["icon"] for action in groupe_actions])

# Generate js file
js_content = "const icons = [\n"
for icon in icons:
    js_content += f'"{icon}",'
js_content += "];\n\nexport default icons;\n"

# Write files
with open("dsfr_hacks/used_icons.js", "w") as js_file:
    js_file.write(js_content)
