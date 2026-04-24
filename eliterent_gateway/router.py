class MicroserviceRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'location_service':
            return 'location_db'
        elif model._meta.app_label == 'diagnostic_service':
            return 'diagnostic_db'
        elif model._meta.app_label == 'payment_service':
            return 'payment_db'
        elif model._meta.app_label in ['auth_service', 'auth', 'contenttypes', 'sessions', 'admin']:
            return 'auth_db'
        return 'default'

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        # On autorise les relations au sein du même microservice
        if obj1._meta.app_label == obj2._meta.app_label:
            return True
        # On autorise les relations avec Auth/Contenttypes car c'est le socle
        base_apps = ['auth', 'auth_service', 'contenttypes', 'sessions']
        if obj1._meta.app_label in base_apps or obj2._meta.app_label in base_apps:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'location_service':
            return db == 'location_db'
        elif app_label == 'diagnostic_service':
            return db == 'diagnostic_db'
        elif app_label == 'payment_service':
            return db == 'payment_db'
        elif app_label in ['auth_service', 'auth', 'contenttypes', 'sessions', 'admin']:
            return db == 'auth_db'
        return db == 'default'
