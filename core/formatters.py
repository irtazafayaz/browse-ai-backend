"""
Log formatters.

Two formatters are provided:

  ConsoleFormatter  — Human-readable, ANSI-coloured output for the terminal.
                      Includes request ID so related lines are easy to group.

  JSONFormatter     — Machine-readable, one-JSON-object-per-line format for
                      production log files and log-aggregation tools
                      (Datadog, CloudWatch, Grafana Loki, etc.).

Example console output
──────────────────────
[2026-03-10 16:01:20] [req-a1b2c3d4] INFO     core.requests            → POST /api/products/search/ | user=anon | body={"query":"lawn"}
[2026-03-10 16:01:21] [req-a1b2c3d4] INFO     products.ai_search       ← AI RESPONSE | status=200 | 1601.6ms
[2026-03-10 16:01:21] [req-a1b2c3d4] WARNING  core.requests            ← POST /api/slow-endpoint/ | status=200 | 3210.4ms | ⚠ SLOW

Example JSON output (one line, pretty-printed here for readability)
────────────────────────────────────────────────────────────────────
{
  "ts":       "2026-03-10T16:01:20.123Z",
  "level":    "INFO",
  "logger":   "core.requests",
  "rid":      "req-a1b2c3d4",
  "app":      "browse-ai-backend",
  "msg":      "→ POST /api/products/search/ | user=anon",
  "method":   "POST",
  "path":     "/api/products/search/",
  "status":   200,
  "duration_ms": 1632.1
}
"""
import json
import logging
from datetime import datetime, timezone


# ── Console (terminal) formatter ─────────────────────────────────────────────

class ConsoleFormatter(logging.Formatter):
    """
    Coloured, human-readable formatter for the development console.

    Line structure:
        [timestamp] [request_id] LEVEL    logger_name    message
    """

    _LEVEL_COLORS = {
        'DEBUG':    '\033[36m',    # cyan
        'INFO':     '\033[32m',    # green
        'WARNING':  '\033[33m',    # yellow
        'ERROR':    '\033[31m',    # red
        'CRITICAL': '\033[1;35m',  # bold magenta
    }
    _RESET = '\033[0m'
    _DIM   = '\033[2m'

    def format(self, record: logging.LogRecord) -> str:
        color = self._LEVEL_COLORS.get(record.levelname, '')
        rid   = getattr(record, 'request_id', '-')
        ts    = self.formatTime(record, '%Y-%m-%d %H:%M:%S')

        level_str  = f'{color}{record.levelname:<8}{self._RESET}'
        logger_str = f'{self._DIM}{record.name:<28}{self._RESET}'
        msg        = record.getMessage()

        if record.exc_info:
            msg += '\n' + self.formatException(record.exc_info)

        return f'[{ts}] [{rid}] {level_str} {logger_str} {msg}'


# ── JSON (file / production) formatter ───────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """
    Structured JSON formatter — one compact JSON object per log line.

    Always emits: ts, level, logger, rid, app, msg.
    Appends optional structured fields when present on the record:
        method, path, status, duration_ms, user
    """

    APP_NAME = 'browse-ai-backend'

    # Extra fields that middleware / ai_search attach via extra={}
    _EXTRA_FIELDS = ('method', 'path', 'status', 'duration_ms', 'user')

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            'ts':     datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'level':  record.levelname,
            'logger': record.name,
            'rid':    getattr(record, 'request_id', '-'),
            'app':    self.APP_NAME,
            'msg':    record.getMessage(),
        }

        for field in self._EXTRA_FIELDS:
            val = getattr(record, field, None)
            if val is not None:
                payload[field] = val

        if record.exc_info:
            payload['exc'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)
