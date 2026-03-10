import json
import logging
from datetime import datetime, timezone


class ConsoleFormatter(logging.Formatter):
    _COLORS = {
        'DEBUG':    '\033[36m',
        'INFO':     '\033[32m',
        'WARNING':  '\033[33m',
        'ERROR':    '\033[31m',
        'CRITICAL': '\033[1;35m',
    }
    _RESET = '\033[0m'
    _DIM   = '\033[2m'

    def format(self, record: logging.LogRecord) -> str:
        color  = self._COLORS.get(record.levelname, '')
        rid    = getattr(record, 'request_id', '-')
        ts     = self.formatTime(record, '%Y-%m-%d %H:%M:%S')
        level  = f'{color}{record.levelname:<8}{self._RESET}'
        name   = f'{self._DIM}{record.name:<28}{self._RESET}'
        msg    = record.getMessage()

        if record.exc_info:
            msg += '\n' + self.formatException(record.exc_info)

        return f'[{ts}] [{rid}] {level} {name} {msg}'


class JSONFormatter(logging.Formatter):
    _EXTRA = ('method', 'path', 'status', 'duration_ms', 'user')

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'ts':     datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'level':  record.levelname,
            'logger': record.name,
            'rid':    getattr(record, 'request_id', '-'),
            'app':    'browse-ai-backend',
            'msg':    record.getMessage(),
        }
        for field in self._EXTRA:
            val = getattr(record, field, None)
            if val is not None:
                payload[field] = val
        if record.exc_info:
            payload['exc'] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
