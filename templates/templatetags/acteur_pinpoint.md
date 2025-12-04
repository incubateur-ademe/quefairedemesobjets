# Pinpoint Acteur

Marqueur de carte pour afficher un acteur avec son action.

## Comment l'utiliser

```django
{% load carte_tags %}
{% acteur_pinpoint_tag acteur=acteur direction=direction action_list=action_list carte=carte sous_categorie_id=sc_id %}
```

### Paramètres du preview

- `action` : Code de l'action (reparer, donner, etc.)
- `avec_bonus` : Filtrer les acteurs avec bonus réparation
- `carte` : Mode carte (True) ou liste (False)
- `carte_config` : Configuration de carte personnalisée (optionnel)
- `acteur_type` : Type d'acteur à filtrer (optionnel)

### Note

Ce composant utilise le template tag `acteur_pinpoint_tag` pour générer dynamiquement le marqueur de carte en fonction des paramètres fournis.
