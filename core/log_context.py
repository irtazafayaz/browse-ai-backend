import uuid
from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar('request_id', default='-')


def new_request_id(incoming: str | None = None) -> str:
    rid = incoming or f'req-{uuid.uuid4().hex[:8]}'
    _request_id.set(rid)
    return rid


def get_request_id() -> str:
    return _request_id.get()
