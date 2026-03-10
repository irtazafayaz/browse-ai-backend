"""
Request / Response logging middleware.

Logs every incoming HTTP request and its response to the 'core.requests' logger:

  REQUEST  POST /api/products/search/ | user=anon | body={"query": "trouser", "page": 1}
  RESPONSE POST /api/products/search/ | status=200 | 342.1ms

The logger name 'core.requests' is wired up in settings.LOGGING so output appears
in the console and can be routed to a file / external sink in production.
"""
import json
import logging
import time

logger = logging.getLogger('core.requests')


class RequestResponseLogMiddleware:
    """WSGI-compatible middleware that logs each request and its response."""

    # Paths to skip (health checks, static files, schema introspection)
    _SKIP_PREFIXES = ('/static/', '/media/', '/favicon')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip noisy, uninteresting paths
        path = request.get_full_path()
        if any(path.startswith(p) for p in self._SKIP_PREFIXES):
            return self.get_response(request)

        start = time.monotonic()

        # ── Log incoming request ────────────────────────────────────────
        body_repr = self._read_body(request)
        user_repr = self._get_user(request)

        logger.info(
            '→ REQUEST  %s %s | user=%s%s',
            request.method,
            path,
            user_repr,
            f' | body={body_repr}' if body_repr else '',
        )

        # ── Process ─────────────────────────────────────────────────────
        response = self.get_response(request)

        # ── Log outgoing response ────────────────────────────────────────
        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            '← RESPONSE %s %s | status=%d | %.1fms',
            request.method,
            path,
            response.status_code,
            duration_ms,
        )

        return response

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _read_body(request) -> str:
        """Return a concise string representation of the request body."""
        content_type = request.content_type or ''
        if 'application/json' not in content_type:
            return ''
        try:
            raw = request.body  # bytes; Django caches this so views still work
            data = json.loads(raw)
            # Truncate long strings inside the body to keep logs readable
            return json.dumps(data, ensure_ascii=False)[:300]
        except Exception:
            return request.body.decode('utf-8', errors='replace')[:300]

    @staticmethod
    def _get_user(request) -> str:
        """Return a short identifier for the requesting user."""
        user = getattr(request, 'user', None)
        if user is None:
            return 'anon'
        if hasattr(user, 'is_authenticated') and user.is_authenticated:
            return str(getattr(user, 'id', user))
        return 'anon'
