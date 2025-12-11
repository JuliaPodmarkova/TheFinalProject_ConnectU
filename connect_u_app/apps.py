from django.apps import AppConfig

class ConnectUAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'connect_u_app'

    def ready(self):
        import connect_u_app.signals