from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = 'blog'

    def ready(self):
        try:
            from core.db import ensure_indexes
            ensure_indexes()
        except Exception:
            pass
