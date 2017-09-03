from datetime import datetime
from ftw.structlog.collector import collect_data_to_log
from ftw.structlog.logger import log_request_data
from threading import local
from tzlocal import get_localzone
import logging
import pytz
import time


LOG_TZ = get_localzone()

root_logger = logging.root


# Thread-local object to keep track of request duration
timing = local()
timing.pub_start = None
timing.timestamp = None


def handle_pub_start(event):
    """Handle IPubStart events: Keep track of time when request started.
    """
    global timing
    # Get time in UTC, make non-naive, and convert to local time for logging
    ts = datetime.utcnow().replace(tzinfo=pytz.utc)
    timing.timestamp = ts.astimezone(LOG_TZ).isoformat()
    timing.pub_start = time.time()


def handle_pub_end(event):
    """Handle IPubSuccess or IPubFailure events.

    Log the request, being very careful not to cause any unhandled exceptions
    as a side effect of logging.
    """
    try:
        log_request(event)
    except Exception as exc:
        root_logger.warn('Failed to log request using ftw.structlog: %r' % exc)


def log_request(event):
    global timing
    request = event.request

    request_data = collect_data_to_log(timing, request)
    log_request_data(request_data)
