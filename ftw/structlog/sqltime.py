from sqlalchemy.event import listen
from zope.annotation import IAnnotations
from zope.globalrequest import getRequest
import time


def before_cursor_execute(conn, cursor, statement,
                          parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())


def after_cursor_execute(conn, cursor, statement,
                         parameters, context, executemany):
    if 'query_start_time' not in conn.info:
        return

    if len(conn.info['query_start_time']) > 1:
        # Ignore any inner queries (in case of nested cursor execute events)
        conn.info['query_start_time'].pop(-1)
        return

    query_time = time.time() - conn.info['query_start_time'].pop(-1)

    # Track cumulative query execution time in request annotations,
    # for it to be collected later when logging the request.
    request = getRequest()
    if request:
        ann = IAnnotations(request)
        ann['sql_query_time'] = ann.get('sql_query_time', 0) + query_time


def register_query_profiling_listeners(event):
    """Register event listeners to track query execution time.

    Based on https://docs.sqlalchemy.org/en/13/faq/performance.html#query-profiling
    """
    engine = event.engine

    listen(engine, 'before_cursor_execute', before_cursor_execute)
    listen(engine, 'after_cursor_execute', after_cursor_execute)
