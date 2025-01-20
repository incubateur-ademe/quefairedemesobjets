"""Tests pour vérifier la compatibilité
des packages utilisés par Airflow

Contexte: au 2025-01-15 via PR1200 on est confronté au
problème suivant:
    🟢 les tests dags_unit_tests/ fonctionnent
    🟢 la CI Github fonctionne
    🔴 Mais les DAGs échouent car pandas 2.2.3 casse la
    compatibilité avec notre Engine SQLAlchemy

D'où des tests python, indépendents des DAGs Airflow et la CI
pour vérifier les compatibilités de base
"""

import pandas as pd
from sqlalchemy import create_engine


def test_pandas_read_sql_table():
    """Au 2025-01-15 ce test fonctionne en pandas 2.1.4 mais
    échoue en 2.2.3 avec l'erreur suivante:
    AttributeError: 'Engine' object has no attribute 'cursor'

    TODO: lorsque ce test échoue à l'avenir à cause d'une upgrade pandas,
    penser à:
     - mettre à jour ce teste pour qu'il fonctionne
     - mettre à jour les codes DAGs pour qu'ils fonctionnent également
    """
    print(f"Pandas version: {pd.__version__}")
    engine = create_engine("sqlite:///:memory:")
    engine.execute("CREATE TABLE my_table (id INT, name TEXT)")
    pd.read_sql_table("my_table", engine)
