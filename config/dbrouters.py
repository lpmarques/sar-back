class AppDBRouter(object):
    """
    A router to control all database operations on models from
    different applications.
    """
    schemas = ['core', 'geography', 'catalog', 'agroforestry']

    def db_for_read(self, model, **hints):
        # Attempts to read any model go to default database (wide search_path).
        return 'default'

    def db_for_write(self, model, **hints):
        # Attempts to write to any model go to default database (wide search_path).
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Each app's migrations go to its own schema; 'default' gets the global Django tables.
        if db == 'default':
            return app_label not in self.schemas
        
        return db == app_label
