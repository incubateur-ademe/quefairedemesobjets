class DatabaseRouter:
    """
    Routeur de base de données pour gérer les migrations sur la base de données readonly
    """

    def db_for_read(self, model, **hints):
        """
        Suggère la base de données à utiliser pour les opérations de lecture.
        """
        return "readonly"

    def db_for_write(self, model, **hints):
        """
        Suggère la base de données à utiliser pour les opérations d'écriture.
        """
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """
        Autorise les relations entre les objets.
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Détermine si la migration doit s'exécuter sur la base de données spécifiée.
        """
        # Si la migration spécifie explicitement une base de données, on l'utilise
        if "database" in hints:
            return db == hints["database"]

        # Par défaut, on utilise la base de données par défaut
        return db == "default"
