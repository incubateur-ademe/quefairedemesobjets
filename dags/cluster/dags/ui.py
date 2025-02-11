"""
Code nécessaire pour le formattage de la UI Airflow,
qu'on déplace dans ce fichier pour ne pas encombrer
le DAG
"""

UI_PARAMS_SEPARATOR_SELECTION_ACTEURS = r"""

---

# 🔎 Paramètres **sélection acteurs non-parent**
Les paramètres suivants décident des acteurs non-parent à inclure
ou exclure comme candidats au clustering. Ce n'est pas
parce qu'un acteur est selectionné qu'il sera forcément clusterisé
(ex: si il se retrouve tout seul sachant qu'on supprime
les clusters de taille 1)
"""

UI_PARAMS_SEPARATOR_SELECTION_PARENTS = r"""

---

# 🔎 Paramètres **sélection parents existants**
Les paramètres suivants décident des parents à inclure
ou exclure comme candidats au clustering.

 - 💯 Par défault on prend **TOUS les parents** des **mêmes acteur-types
 utilisés pour les acteurs**
 - Et on filtre ces parents avec les paramètres suivants:
"""

UI_PARAMS_SEPARATOR_NORMALIZATION = r"""

---

# 🧹 Paramètres de **normalisation acteurs + parents**
Les paramètres suivants définissent comment les valeurs
des champs vont être transformées avant le clustering.
"""

UI_PARAMS_SEPARATOR_CLUSTERING = r"""

---

# 📦 Paramètres de **clustering acteurs + parents**
Les paramètres suivants définissent comment les acteurs
vont être regroupés en clusters.
"""
