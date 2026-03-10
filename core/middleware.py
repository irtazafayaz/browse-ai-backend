import json
import logging
import time

from .log_context import new_request_id

logger = logging.getLogger('core.requests')

_SENSITIVE    = frozenset({'password', 'password2', 'token', 'access_token',
                           'refresh_token', 'secret', 'client_secret', 'api_key'})
_SLOW_MS      = 2_000
_VERY_SLOW_MS = 10_000


class RequestResponseLogMiddleware:
    _SKIP = ('/static/', '/media/', '/favicon')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.get_full_path()
        if any(path.startswith(p) for p in self._SKIP):
            return self.get_response(request)

        rid  = new_request_id(request.headers.get('X-Request-ID'))
        user = _get_user(request)
        body = _read_request_body(request)

        logger.info(
            '→ %s %s | user=%s%s',
            request.method, path, user,
            f' | body={body}' if body else '',
            extra=dict(method=request.method, path=path, user=user),
        )

        t0       = time.monotonic()
        response = self.get_response(request)
        ms       = (time.monotonic() - t0) * 1000

        response['X-Request-ID'] = rid

        extra = dict(method=request.method, path=path,
                     status=response.status_code, duration_ms=round(ms, 1))
        _log_response(request.method, path, response.status_code, ms,
                      _read_response_body(response), extra)

        return response


def _log_response(method, path, status, ms, body, extra):
    suffix = f' | response={body}' if body else ''
    msg    = '← %s %s | status=%d | %.1fms' + suffix
    args   = (method, path, status, ms)
    if ms > _VERY_SLOW_MS:
        logger.error(msg + ' | ⚠ VERY SLOW', *args, extra=extra)
    elif ms > _SLOW_MS:
        logger.warning(msg + ' | ⚠ SLOW', *args, extra=extra)
    else:
        logger.info(msg, *args, extra=extra)


def _read_request_body(request) -> str:
    if 'application/json' not in (request.content_type or ''):
        return ''
    try:
        data = json.loads(request.body)
        if isinstance(data, dict):
            data = {k: '***' if k.lower() in _SENSITIVE else v for k, v in data.items()}
        return json.dumps(data, ensure_ascii=False)[:300]
    except Exception:
        return request.body.decode('utf-8', errors='replace')[:300]


def _read_response_body(response) -> str:
    if getattr(response, 'streaming', False):
        return ''
    if 'application/json' not in response.get('Content-Type', ''):
        return ''
    try:
        data = json.loads(response.content.decode('utf-8', errors='replace'))
        if not isinstance(data, dict):
            return response.content.decode()[:400]
        # Summarise large product lists to keep logs readable
        if 'products' in data and isinstance(data['products'], list):
            return json.dumps({**data, 'products': f'[{len(data["products"])} items]'},
                              ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)[:400]
    except Exception:
        return ''


def _get_user(request) -> str:
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        return str(getattr(user, 'id', user))
    return 'anon'
