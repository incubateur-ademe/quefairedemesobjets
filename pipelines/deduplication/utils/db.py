def db_modify(db_engine, query: str, is_dry_run: bool) -> None:
    """Utilitaire de modification de la base de données
    pour gérer le dry run et éviter d'avoir un code répétitif

    Args:
        db_engine: connexion à la base de données
        query: requête SQL
        is_dry_run: mode test
    """
    print(f"db_modify: {query}")
    print(f"{is_dry_run=}")
    if is_dry_run:
        print("DB: pas de modif en mode test ✋")
        pass
    else:
        db_engine.execute(query)
        print("DB: modification ✅")
