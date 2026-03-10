"""
Custom logging filters.
"""
import logging

from .log_context import get_request_id


class RequestIDFilter(logging.Filter):
    """
    Injects the current request ID into every LogRecord so it is available
    to all formatters as %(request_id)s / {request_id}.

    Install this filter on every handler (not individual loggers) so that
    every log line — from any module — carries the ID for the active request.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
