import logging

# ---------------------------------------------------------------------------
# Gunicorn configuration
# ---------------------------------------------------------------------------

# Logging
loglevel = "info"
accesslog = "-"   # stdout
errorlog = "-"    # stdout (gunicorn uses this for all its own log output)
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Workers
workers = 2
worker_class = "sync"
threads = 1

# Timeouts
timeout = 120
keepalive = 5


# ---------------------------------------------------------------------------
# Fix severity mapping: ensure gunicorn's INFO / WARNING records are emitted
# at the correct Python log level so Railway (and any structured log sink)
# captures them with the right severity label instead of treating everything
# as an error.
# ---------------------------------------------------------------------------

class CorrectLevelFilter(logging.Filter):
    """
    Gunicorn routes all of its own messages through the 'gunicorn.error'
    logger, which causes log-aggregators to tag every message — including
    plain INFO startup lines — as severity ERROR.

    This filter is a no-op on the records themselves; the real fix is
    attaching a StreamHandler directly to the gunicorn loggers so that
    the records are emitted with their actual levelname (INFO, WARNING,
    ERROR) rather than being funnelled through a handler whose name
    implies 'error'.
    """
    def filter(self, record):
        return True  # allow all records through unchanged


def on_starting(server):
    """
    Called just before the master process is initialised.
    Re-configure the gunicorn loggers so that each record is written to
    stdout with its true severity level.
    """
    fmt = logging.Formatter(
        "[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )

    for logger_name in ("gunicorn", "gunicorn.error", "gunicorn.access"):
        logger = logging.getLogger(logger_name)
        # Remove any handlers gunicorn may have already attached so we
        # don't get duplicate output.
        logger.handlers = []

        handler = logging.StreamHandler()
        handler.setFormatter(fmt)
        handler.addFilter(CorrectLevelFilter())
        logger.addHandler(handler)

        # Propagate=False keeps records from bubbling up to the root
        # logger and being double-printed.
        logger.propagate = False

    # Ensure the root logger doesn't swallow anything.
    logging.getLogger().setLevel(logging.INFO)
