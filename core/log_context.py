"""
Request-scoped context storage.

Uses Python's contextvars so the request ID is automatically isolated per
thread (WSGI) and per async task (ASGI) without any manual threading.local
management.
"""
import uuid
from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar('request_id', default='-')


def new_request_id(incoming: str | None = None) -> str:
    """
    Set a new request ID for the current context.
    If the caller passes an upstream X-Request-ID header value, that is
    adopted as-is so the ID can be correlated across services.
    """
    rid = incoming or f'req-{uuid.uuid4().hex[:8]}'
    _request_id.set(rid)
    return rid


def get_request_id() -> str:
    """Return the request ID for the currently executing request, or '-'."""
    return _request_id.get()
