"""
Request / Response logging middleware.

Responsibilities
────────────────
1. Request ID      — Generates a unique `req-<8hex>` ID per request, or adopts an
                     upstream `X-Request-ID` header so IDs can be correlated across
                     services. The ID is stored via contextvars so every log line
                     emitted during the request automatically carries it.

2. Payload logging — Logs the incoming request body (sanitised) and the outgoing
                     response body (summarised), so the full round-trip is visible
                     in one request-ID group.

3. Slow alerts     — Emits WARNING when a response exceeds 2 s and ERROR when it
                     exceeds 10 s, making latency regressions immediately visible.

4. Redaction       — Strips sensitive fields (password, token, secret, …) from
                     request body logs so credentials never appear in plain text.

5. Response header — Echoes `X-Request-ID` back to the client, enabling
                     end-to-end tracing from browser / mobile.

Example output
──────────────
→ POST /api/products/search/ | user=anon | body={"query":"pant","page":1}
← POST /api/products/search/ | status=200 | 1632ms | response={"products":[10 items],"total":41,"page":1,"has_next":true}

→ POST /api/auth/login/ | user=anon | body={"email":"x@x.com","password":"***"}
← POST /api/auth/login/ | status=400 | 44ms | response={"detail":"Invalid credentials."}
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
    """WSGI middleware: request-ID propagation + full request/response logging."""

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

        # ── 2. Log incoming request + payload ────────────────────────────
        user = _get_user(request)
        req_body = _read_request_body(request)

        logger.info(
            '→ %s %s | user=%s%s',
            request.method, path, user,
            f' | body={req_body}' if req_body else '',
            extra=dict(method=request.method, path=path, user=user),
        )

        # ── 3. Process request ───────────────────────────────────────────
        t0 = time.monotonic()
        response = self.get_response(request)
        ms = (time.monotonic() - t0) * 1000

        # ── 4. Echo request ID back to the client ────────────────────────
        response['X-Request-ID'] = rid

        # ── 5. Log response + body ───────────────────────────────────────
        res_body = _read_response_body(response)
        extra = dict(
            method=request.method, path=path,
            status=response.status_code, duration_ms=round(ms, 1),
        )
        _log_response(request.method, path, response.status_code, ms, res_body, extra)

        return response


# ── Helpers ───────────────────────────────────────────────────────────────────

def _log_response(
    method: str, path: str, status: int, ms: float,
    body: str, extra: dict,
) -> None:
    suffix = f' | response={body}' if body else ''
    base   = '← %s %s | status=%d | %.1fms' + suffix
    args   = (method, path, status, ms)

    if ms > _VERY_SLOW_MS:
        logger.error(base + ' | ⚠ VERY SLOW', *args, extra=extra)
    elif ms > _SLOW_MS:
        logger.warning(base + ' | ⚠ SLOW', *args, extra=extra)
    else:
        logger.info(base, *args, extra=extra)


def _read_request_body(request) -> str:
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


def _read_response_body(response) -> str:
    """
    Return a compact representation of the response body.

    - Non-JSON responses    → ''  (skip binary, HTML, etc.)
    - Streaming responses   → ''  (cannot safely read)
    - Paginated products    → compact summary  {"products":[N items],"total":X,...}
    - Error / small JSON    → full body, truncated to 400 chars
    """
    if getattr(response, 'streaming', False):
        return ''
    content_type = response.get('Content-Type', '')
    if 'application/json' not in content_type:
        return ''
    try:
        raw = response.content.decode('utf-8', errors='replace')
        data = json.loads(raw)

        if not isinstance(data, dict):
            return raw[:400]

        # Summarise paginated product responses — the full list is too large
        if 'products' in data and isinstance(data['products'], list):
            summary = {
                'products': f'[{len(data["products"])} items]',
                **{k: v for k, v in data.items() if k != 'products'},
            }
            return json.dumps(summary, ensure_ascii=False)

        # Everything else: show in full, truncated
        return raw[:400]

    except Exception:
        return ''


def _get_user(request) -> str:
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        return str(getattr(user, 'id', user))
    return 'anon'
