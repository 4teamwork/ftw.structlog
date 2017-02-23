from datetime import datetime
from ftw.jsonlog.logger import setup_logger
from threading import local
import json
import logging
import time


json_log = setup_logger()
root_logger = logging.root


# Thread-local object to keep track of request duration
timing = local()
timing.pub_start = None


def handle_pub_start(event):
    global timing
    timing.pub_start = time.time()


def handle_pub_success(event):
    try:
        log_request(event)
    except Exception as exc:
        root_logger.warn('Failed to log request using ftw.jsonlog: %r' % exc)


def log_request(event):
    request = event.request

    logdata = collect_data_to_log(request)
    msg = json.dumps(logdata, sort_keys=True)
    json_log.info(msg)


def collect_data_to_log(request):
    global timing
    duration = time.time() - timing.pub_start
    timing.pub_start = None

    timestamp = datetime.now().isoformat()
    logdata = {
        'host': request.environ.get('REMOTE_ADDR'),
        'user': get_username(request),
        'timestamp': timestamp,
        'method': request.method,
        'url': request.get('ACTUAL_URL'),
        'status': request.response.getStatus(),
        'bytes': get_content_length(request),
        'duration': duration,
        'referer': request.environ.get('HTTP_REFERER'),
        'user_agent': request.environ.get('HTTP_USER_AGENT'),
    }
    return logdata


def get_content_length(request):
    content_length = request.response.getHeader('Content-Length')
    if content_length:
        return int(content_length)


def get_username(request):
    user = request.get('AUTHENTICATED_USER')
    if user:
        return user.getUserName()
