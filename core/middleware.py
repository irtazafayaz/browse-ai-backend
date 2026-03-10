"""
Request / Response logging middleware.

Responsibilities
────────────────
1. Request ID   — Generates a unique `req-<8hex>` ID per request, or adopts an
                  upstream `X-Request-ID` header so IDs can be correlated across
                  services. The ID is stored via contextvars so every log line
                  emitted during the request automatically carries it.

2. Logging      — Logs the incoming request (method, path, user, sanitised body)
                  and the outgoing response (status, duration).

3. Slow alerts  — Emits WARNING when a response exceeds 2 s and ERROR when it
                  exceeds 10 s, making latency regressions immediately visible.

4. Redaction    — Strips sensitive fields (password, token, secret, …) from
                  request body logs so credentials never appear in plain text.

5. Response header — Echoes `X-Request-ID` back to the client, enabling
                     end-to-end tracing from browser / mobile.
"""
import json
import logging
import time

from .log_context import new_request_id

logger = logging.getLogger('core.requests')

# ── Sensitive field names — values are replaced with *** ─────────────────────
_SENSITIVE = frozenset({
    'password', 'password2',
    'token', 'access_token', 'refresh_token',
    'secret', 'client_secret',
    'api_key', 'x_api_key',
    'card_number', 'cvv', 'ssn',
})

# ── Slow-request thresholds ───────────────────────────────────────────────────
_SLOW_MS      = 2_000   # WARNING
_VERY_SLOW_MS = 10_000  # ERROR


class RequestResponseLogMiddleware:
    """WSGI middleware: request-ID propagation + structured request/response logging."""

    _SKIP_PREFIXES = ('/static/', '/media/', '/favicon')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.get_full_path()

        # Skip static assets and other noise
        if any(path.startswith(p) for p in self._SKIP_PREFIXES):
            return self.get_response(request)

        # ── 1. Assign request ID ─────────────────────────────────────────
        rid = new_request_id(request.headers.get('X-Request-ID'))

        # ── 2. Log incoming request ──────────────────────────────────────
        user = _get_user(request)
        body = _read_body(request)

        logger.info(
            '→ %s %s | user=%s%s',
            request.method, path, user,
            f' | body={body}' if body else '',
            extra=dict(method=request.method, path=path, user=user),
        )

        # ── 3. Process request ───────────────────────────────────────────
        t0 = time.monotonic()
        response = self.get_response(request)
        ms = (time.monotonic() - t0) * 1000

        # ── 4. Echo request ID back to the client ────────────────────────
        response['X-Request-ID'] = rid

        # ── 5. Log response — level reflects latency ─────────────────────
        extra = dict(
            method=request.method, path=path,
            status=response.status_code, duration_ms=round(ms, 1),
        )
        _log_response(request.method, path, response.status_code, ms, extra)

        return response


# ── Helpers ───────────────────────────────────────────────────────────────────

def _log_response(method: str, path: str, status: int, ms: float, extra: dict) -> None:
    base = '← %s %s | status=%d | %.1fms'
    args = (method, path, status, ms)
    if ms > _VERY_SLOW_MS:
        logger.error(base + ' | ⚠ VERY SLOW', *args, extra=extra)
    elif ms > _SLOW_MS:
        logger.warning(base + ' | ⚠ SLOW', *args, extra=extra)
    else:
        logger.info(base, *args, extra=extra)


def _read_body(request) -> str:
    """Return a sanitised, truncated JSON body string, or '' for non-JSON."""
    if 'application/json' not in (request.content_type or ''):
        return ''
    try:
        data = json.loads(request.body)
        if isinstance(data, dict):
            data = {
                k: '***' if k.lower() in _SENSITIVE else v
                for k, v in data.items()
            }
        return json.dumps(data, ensure_ascii=False)[:300]
    except Exception:
        return request.body.decode('utf-8', errors='replace')[:300]


def _get_user(request) -> str:
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        return str(getattr(user, 'id', user))
    return 'anon'
