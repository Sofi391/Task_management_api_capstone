from django.apps import AppConfig


class TaskApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'task_api'
    def ready(self):
        from . import signals


