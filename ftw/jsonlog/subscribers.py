from datetime import datetime
from ftw.jsonlog.logger import setup_logger
from threading import local
from zope.component.hooks import getSite
import json
import logging
import time


json_log = setup_logger()
root_logger = logging.root


# Thread-local object to keep track of request duration
timing = local()
timing.pub_start = None
timing.timestamp = None


def handle_pub_start(event):
    global timing
    timing.timestamp = datetime.now().isoformat()
    timing.pub_start = time.time()


def handle_pub_end(event):
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

    logdata = {
        'host': request.getClientAddr(),
        'site': get_site_id(),
        'user': get_username(request),
        'timestamp': timing.timestamp,
        'method': request.method,
        'url': get_url(request),
        'status': request.response.getStatus(),
        'bytes': get_content_length(request),
        'duration': duration,
        # TODO: Always return empty string if no referrer
        'referer': request.environ.get('HTTP_REFERER'),
        'user_agent': request.environ.get('HTTP_USER_AGENT'),
    }

    return logdata


def get_content_length(request):
    content_length = request.response.getHeader('Content-Length')
    if content_length:
        return int(content_length)


def get_site_id():
    site = getSite()
    if site:
        return site.id
    return ''


def get_username(request):
    user = request.get('AUTHENTICATED_USER')
    if user:
        return user.getUserName()


def get_url(request):
    url = request.get('ACTUAL_URL')
    qs = request.get('QUERY_STRING')
    if qs:
        url = url + "?" + qs
    return url
