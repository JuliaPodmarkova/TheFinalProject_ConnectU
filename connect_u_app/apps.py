# connect_u_app/apps.py

from django.apps import AppConfig

class ConnectUAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'connect_u_app'

    def ready(self):
        # Импортируем сигналы здесь, чтобы они были зарегистрированы при запуске приложения
        import connect_u_app.signals