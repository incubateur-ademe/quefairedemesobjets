# Documentation de l'injestion et du traitement des base de données LVAO

## SINOE

### SINOE - Injestion

Sur la base de données MySQL (cf. docker-compose.yml)

- Créer une base de données SINOE
- Executer le sql `export.sql`

8674 Points référencés

### SINOE - Interpretation

Tables:

- ACTEUR : Lieu (et entreprise) de collecte
- TYP_ACTEUR : Type d'acteur
- V_COMPLEM_ACTEUR : Pivot C_ACTEUR, C_QUESTION ressemble à une selection dans une liste / L_REPONSE ressemble à une liste de code
C'est dans cette liste réponse qu'on trouvera les correspondances entre les codes Sinoe et Taxo quand C_QUESTION= 'Réseau d\'appartenance et activité du site'

Valeur à associer à l'acteur du réemploi:

- AD_LOV : utile ?
- AD_VALLOV : utile ?

Exemple de requête:

```sql
SELECT
  *
FROM
  ACTEUR A
  JOIN V_COMPLEM_ACTEUR AS C ON A.C_ACTEUR = C.C_ACTEUR
  JOIN AD_VALLOV ON C.L_REPONSE = AD_VALLOV.VA_VALLOV
  JOIN AD_LOV ON AD_VALLOV.C_LOV = AD_LOV.C_LOV
WHERE
  A.C_ACTEUR in (49039, 10071)
```

### Via le site www.SINOE.org

Téléchargement possible des acteurs du réemploi va l'interface

## CMA

### CMA - Injestion

Sur la base de données MySQL (cf. docker-compose.yml)

- Créer une base de données CMA
- Executer le sql `export.sql`

130647 Points référencés

### CMA - Interpretation

select siret, name, naf_code, is_reparactor from t_craftsperson as c JOIN t_craftsperson_has_naf_code as naf on c.id = naf.id_craftsperson;
