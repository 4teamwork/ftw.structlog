from zope.component.hooks import getSite
import time


def collect_data_to_log(timing, request):
    """Collect information to be logged, and return it as a Python dict.

    Using the request and timing information, extract all necessary infos
    that should be logged, and prepare them so they can be easily serialized.

    ``timing`` is a module-global, thread-local object kept in
    ftw.structlog.subscribers that is used to track request timing information.
    """
    duration = time.time() - timing.pub_start
    timing.pub_start = None

    request_data = {
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
    return request_data


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
