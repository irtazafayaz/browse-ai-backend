from django.apps import AppConfig


class ProductsConfig(AppConfig):
    name = 'products'

    def ready(self):
        try:
            from core.db import ensure_indexes
            ensure_indexes()
        except Exception:
            # Atlas may be unreachable at boot (dev, CI, cold start).
            # Indexes will be created on the first successful request instead.
            pass
