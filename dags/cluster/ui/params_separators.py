"""
Code nécessaire pour le formattage de la UI Airflow,
qu'on déplace dans ce fichier pour ne pas encombrer
le DAG
"""

READ_ACTEURS = r"""

---

# 🔎 CANDIDATS: **acteurs non-parent** ⬇️
Les paramètres suivants décident des acteurs non-parent à inclure
ou exclure comme candidats au clustering. Ce n'est pas
parce qu'un acteur est selectionné qu'il sera forcément clusterisé
(ex: si il se retrouve tout seul sachant qu'on supprime
les clusters de taille 1)
"""

READ_PARENTS = r"""

---

# 🔎 CANDIDATS: **parents existants** ⬇️
Les paramètres suivants décident des parents à inclure
ou exclure comme candidats au clustering.

 - 💯 Par défault on prend **TOUS les parents** des **mêmes acteur-types
 utilisés pour les acteurs**
 - Et on filtre ces parents avec les paramètres suivants:
"""

NORMALIZATION = r"""

---

# 🧹 NORMALIZATION: **tous les acteurs** ⬇️
Les paramètres suivants définissent comment les valeurs
des champs vont être transformées avant le clustering.
"""

CLUSTERING = r"""

---

# 📦 CLUSTERING: **règles de regroupement** ⬇️
Les paramètres suivants définissent comment les acteurs
vont être regroupés en clusters.
"""

DEDUP_CHOOSE_PARENT = r"""

# 1️⃣ DEDUP: **choix du parent** ⬇️

Pas de paramètres customisables.

📏 Règles:
 - Si 0 parent -> on en crée un
 - Si 1 parent -> on le conserve
 - Si 2+ parents -> on conserve celui avec le + d'enfants
"""

DEDUP_ENRICH_PARENT = r"""

---

# 🪙 DEDUP: **enrichissement du parent** ⬇️
Les paramètres suivants définissent quelles données
vont être proposées pour enrichir le parent choisi

📏 Règles:
 - Si source exclue = ne **PAS** prendre
 - Si donnée vide ET `keep_empty = False` ne **PAS** prendre
 - Si donnée vide ET `keep_empty = True` ET source prio = **PRENDRE**
 - Si source prio = prendre **DE PREFERENCE** en fonction de ci-dessus
 - Si source non-prio = prendre **EN DERNIER RECOURS** après sources prio
"""
