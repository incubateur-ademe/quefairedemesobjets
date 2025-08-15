# Gestion des identifiants

## A savoir

On nomme `source` les partenaires qui partage des listes d'acteur de l'économie circulaire

## Identifiant externe

l'identifiant externe est l'identifiant fournit par le partenaire qui partage l'acteur, cet identifiant n'est pas modfiable pour identifier les mises à jour de l'acteur par le partenaire et pour que la plateforme data ne perde pas les corrections et regroupement d'acteur (clustering)

## Identifiant unique

l'identifiant unique est l'identifiant utilisé par la plateforme pour identifier un acteur.
Cet identifiant est la clé primaire de la table acteur et est utilisé comme clé étrangère par les objets liés à l'acteur

L'identifiant unique est composé comme suit : <SOURCE*CODE>*<IDENTIFIANT_EXTERNE><\_d?>(pour les acteurs digitaux)

- SOURCE_CODE : le code associé au partenaire ayant partagé l'acteur
- IDENTIFIANT_EXTERNE : l'identifiant fournit par la source
- \_d : préfix quand il s'agit d'un acteur digital car les partenaires peuvent partager deux fois le même acteur si celui-ci a une activité physique et en ligne

## Mapping

Il peut arriver que le partenaire ne puisse pas assurer la continuité des identifiants externes. Dans ce cas, si ce partenaire fournit une table de correspondance des anciens identifiants et des nouveux identifiants, alors il est possible d'assurer la continuité des identifiants uniques en exécutant la procédure définie [ici](../../comment-faire/administration/update-ext-id.md)
