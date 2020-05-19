from inspect import ismethod
from zope.annotation import IAnnotations
from zope.component.hooks import getSite
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserView
import time


try:
    from plone.rest.interfaces import IService
except ImportError:
    class IService(Interface):
        pass


VIEW_GROUP_MARKERS = [
    '++resource++',
    '++theme++',
    'portal_css',
    'portal_javascripts',
]


def collect_data_to_log(timing, request):
    """Collect information to be logged, and return it as a Python dict.

    Using the request and timing information, extract all necessary infos
    that should be logged, and prepare them so they can be easily serialized.

    ``timing`` is a module-global, thread-local object kept in
    ftw.structlog.subscribers that is used to track request timing information.
    """
    duration = time.time() - timing.pub_start
    timing.pub_start = None

    try:
        view_name = get_view_name(request)
    except Exception:
        view_name = None

    request_data = {
        'host': request.getClientAddr(),  # deprecated, client_ip should be used instead
        'client_ip': request.getClientAddr(),
        'site': get_site_id(),
        'user': get_username(request),
        'timestamp': timing.timestamp,
        'method': request.method,
        'url': get_url(request),
        'status': request.response.getStatus(),
        'bytes': get_content_length(request),
        'duration': duration,
        'referer': request.environ.get('HTTP_REFERER', ''),
        'user_agent': request.environ.get('HTTP_USER_AGENT'),
        'view': view_name,
    }

    sql_query_time = IAnnotations(request).get('sql_query_time')
    if sql_query_time:
        request_data['sql_query_time'] = sql_query_time

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


def canonicalize_browserview_name(view_name):
    if view_name.startswith('@@'):
        return view_name[2:]
    return view_name


def get_view_name(request):
    path = request['PATH_INFO']

    # Short circuit certain common view groups early, and consolidate them
    # under a group name (mainly CSS and JS resources).
    #
    # We don't want to log each individual resource name, since that would
    # blow up the range of possible values for the view name with highly
    # dynamic data, and would negatively affect compression or indexing of
    # these logs in ES.
    for marker in VIEW_GROUP_MARKERS:
        if marker in path:
            return marker

    published = request.get('PUBLISHED')

    # plone.rest service
    if IService.providedBy(published):
        service = published
        # GET_application_json_@named-service
        full_service_name = str(service.__name__)
        service_name = full_service_name.replace(request._rest_service_id, '')

        # Unnamed service
        if service_name == '':
            return 'context'

        return service_name

    if ismethod(published):
        # Handle methods on views published via allowed_attributes.
        parents = request.get('PARENTS')
        if parents and IBrowserView.providedBy(parents[0]):
            view_name = '/'.join(request.steps[-2:])
            return canonicalize_browserview_name(view_name)

    if request.steps:
        # Fall back to looking at the the rightmost path segment
        view_name = request.steps[-1]

        # Probably a legacy publishing mechanism, like DTML templates.
        # Don't attempt to resolve any further.
        if view_name == 'index_html':
            return None

        return canonicalize_browserview_name(view_name)
