# Mettre à jour les identifiants externe

Parfois Nos partenaires fournisseurs de données ne peuvent pas assurer la continuitédes identifiant qu'ils utilisent.
Il se peut qu'ils nous fournissent une table de correspondance d'identifiants.
Dans ce cas, nous devont modifier les identifiants exetrne des acteurs concernés pour garantir la continuité des acteurs, i.e. garder les corrections et le regroupement des acteurs de cette source
Cette action n'est pas disponible via l'interface, ce "how-to" explique comment procéder à cette modification

## pre-requis

l'action doit-être effectuée par un utilisateur ayant accès à la plateforme de production (Développeur de l'application par exemple)

## Procédure

Convertir la table de mapping en json avec les anciens identifiants externes comme clé et les nouveaux comme valeurs

```json
{
  "old1": "new1",
  "old2": "new2"
}
```

Créer un conteneur "one-off" avec ce fichier

```sh
scalingo --region osc-fr1 --app quefairedemesobjets run --file <MY-FILE>.json bash
```

Le fichier est stocké dans le dossier `/tmp/uploads/` du conteneur

Lancer la commande de conversion des identifiants externes

/tmp/uploads/my-file.json

```sh
python manage.py update_external_ids --source-code <SOURCE_CODE> --mapping-file /tmp/uploads/<MY-FILE>.json
```
