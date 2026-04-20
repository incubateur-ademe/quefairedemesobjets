"""Tests pour vérifier la compatibilité
des packages utilisés par Airflow

Contexte: au 2025-01-15 via PR1200 on est confronté au
problème suivant:
    🟢 les tests dags/tests/ fonctionnent
    🟢 la CI Github fonctionne
    🔴 Mais les DAGs échouent car pandas 2.2.3 casse la
    compatibilité avec notre Engine SQLAlchemy

D'où des tests python, indépendents des DAGs Airflow et la CI
pour vérifier les compatibilités de base
"""

import sqlite3

import pandas as pd


def test_pandas_read_sql_table():
    """Vérifie que pandas peut lire une table via une connexion sqlite3.

    Historique:
    - pandas 2.1.4 : OK avec SQLAlchemy engine.execute() + read_sql_table(engine)
    - pandas 2.2+ / SQLAlchemy 1.4 : incompatible (Engine.cursor supprimé côté pandas)
    - Solution : passer une connexion sqlite3 DBAPI2, supportée par toutes versions
    """
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE my_table (id INT, name TEXT)")
    pd.read_sql("SELECT * FROM my_table", con)
