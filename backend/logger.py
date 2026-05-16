"""
FinMind Logger
─────────────────────────────────────────────────────────────────
Structured JSON logs  → logs/finmind_YYYY-MM-DD.log
Human-readable console → colored, prefixed by level
Rotating daily files   → keeps last 7 days automatically
"""
'''JSON logs make sense when:

->You ship logs to an external service (Datadog, Loki, CloudWatch)
->Multiple services are writing logs and you need to correlate them
->You're running in production with high traffic and need alerting on specific fields'''

import logging
import json
import sys
import os
import time
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from typing import Any

# ── Paths ─────────────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "finmind.log")   # handler adds date suffix

# ── ANSI colors for console ────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
COLORS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
}

# ── Console formatter (human-readable, colored) ────────────────────────────────
class ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color  = COLORS.get(record.levelname, RESET)
        ts     = datetime.now().strftime("%H:%M:%S")
        level  = f"{color}{BOLD}{record.levelname:<8}{RESET}"
        logger = f"\033[90m[{record.name}]{RESET}"

        base = f"{ts} {level} {logger} {record.getMessage()}"

        # Attach any extra fields passed as kwargs
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in logging.LogRecord(
                "", 0, "", 0, "", (), None
            ).__dict__ and k not in ("message", "asctime")
        }
        if extras:
            extra_str = "  " + "  ".join(f"\033[90m{k}={v}{RESET}" for k, v in extras.items())
            base += extra_str

        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)

        return base


# ── JSON formatter (machine-readable, for log files) ──────────────────────────
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base_fields = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)
        base_fields.update({"message", "asctime"})

        payload: dict[str, Any] = {
            "ts":      datetime.now(timezone.utc).isoformat(),
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
            "module":  record.module,
            "func":    record.funcName,
            "line":    record.lineno,
        }

        # Extra fields (e.g. route=, status_code=, duration_ms=)
        extras = {k: v for k, v in record.__dict__.items() if k not in base_fields}
        if extras:
            payload["extra"] = extras

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, ensure_ascii=False)


# ── Build the logger ──────────────────────────────────────────────────────────
def _build_logger(name: str = "finmind") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:          # avoid duplicate handlers on reload
        return logger

    # 1. Console handler — INFO and above, colored
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(ConsoleFormatter())
    logger.addHandler(ch)

    # 2. File handler — DEBUG and above, JSON, rotates daily, keeps 7 days
    fh = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        utc=True,
    )
    fh.suffix = "%Y-%m-%d"       # finmind.log.2025-05-10
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(JSONFormatter())
    logger.addHandler(fh)

    return logger


log = _build_logger()


# ── Convenience helpers ───────────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    """Return a child logger, e.g. get_logger('routes.expenses')"""
    return logging.getLogger(f"finmind.{name}")


# ── FastAPI middleware helper ─────────────────────────────────────────────────
async def log_requests(request, call_next):
    """
    Middleware: logs every request + response with timing.

    Usage in main.py:
        from logger import log_requests
        app.middleware("http")(log_requests)
    """
    start = time.perf_counter()
    req_id = f"{int(time.time()*1000) % 100000:05d}"   # short 5-digit ID

    log.info(
        f"→ {request.method} {request.url.path}",
        extra={
            "req_id":      req_id,
            "method":      request.method,
            "path":        request.url.path,
            "query":       str(request.url.query) or None,
            "client_ip":   request.client.host if request.client else "unknown",
        }
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        duration = round((time.perf_counter() - start) * 1000, 1)
        log.error(
            f"✗ UNHANDLED {request.method} {request.url.path} — {exc}",
            exc_info=True,
            extra={"req_id": req_id, "duration_ms": duration}
        )
        raise

    duration = round((time.perf_counter() - start) * 1000, 1)
    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    log.log(
        level,
        f"← {response.status_code} {request.method} {request.url.path}  ({duration}ms)",
        extra={
            "req_id":      req_id,
            "status_code": response.status_code,
            "duration_ms": duration,
        }
    )
    return response
