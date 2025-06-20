"""
Router de base de données pour les tests
Empêche les migrations warehouse pendant les tests
"""


class TestDatabaseRouter:
    """
    Router pour diriger les requêtes et migrations lors des tests
    """

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Empêche toute migration vers warehouse pendant les tests
        """
        if db == "warehouse":
            return False
        return True

    def db_for_read(self, model, **hints):
        """Utilise la base par défaut pour les lectures pendant les tests"""
        return "default"

    def db_for_write(self, model, **hints):
        """Utilise la base par défaut pour les écritures pendant les tests"""
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """Autorise toutes les relations pendant les tests"""
        return True
