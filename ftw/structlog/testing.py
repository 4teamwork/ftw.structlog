from App.config import getConfiguration
from contextlib import contextmanager
from ftw.structlog.logger import setup_logger
from ftw.testbrowser import REQUESTS_BROWSER_FIXTURE
from logging import getLogger
from plone.app.testing import FunctionalTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.testing import z2
from StringIO import StringIO
from zope.configuration import xmlconfig
import logging
import os
import pytz
import tempfile
import ZConfig


def get_log_path():
    """Get filesystem path to ftw.structlog's logfile.
    """
    logger = getLogger('ftw.structlog')
    if logger.handlers:
        log_path = logger.handlers[0].stream.name
        return log_path


@contextmanager
def env_var(name, value):
    assert name not in os.environ, \
        'Unexpectedly found the variable {} in the environment.'.format(name)
    os.environ[name] = value
    try:
        yield
    finally:
        os.environ.pop(name)


class PatchedLogTZ(object):
    """Context manager that patches LOG_TZ to a given timezone.
    """

    def __init__(self, tzname):
        self.new_tz = pytz.timezone(tzname)

    def __enter__(self):
        from ftw.structlog import subscribers
        self._original_log_tz = subscribers.LOG_TZ
        subscribers.LOG_TZ = self.new_tz
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        from ftw.structlog import subscribers
        subscribers.LOG_TZ = self._original_log_tz


class StructLogLayer(PloneSandboxLayer):

    def setUp(self):
        # Keep track of temporary files we create
        self._created_tempfiles = []
        super(StructLogLayer, self).setUp()

    def tearDown(self):
        super(StructLogLayer, self).tearDown()

        # Clean up all temporary files we created
        while self._created_tempfiles:
            os.unlink(self._created_tempfiles.pop())

        # Remove any log handlers that were set up
        logger = logging.getLogger('ftw.structlog')
        map(logger.removeHandler, logger.handlers)

    def mktemp(self):
        """Create a temporary file to use as the path for the eventlog.

        We don't actually care about the contents of this file, we just need
        it to get a valid writable path to pass to the eventlog config, so
        ftw.contentstats can derive its own logfile path from it.

        The filename mimics the instance eventlog's filename though, so that
        ftw.structlog can recognize the filename format and derive a filename
        with its own '-json.log' suffix.
        """
        fd, fn = tempfile.mkstemp(prefix='instance0-', suffix='.log')
        os.close(fd)
        self._created_tempfiles.append(fn)
        return fn

    def setup_eventlog(self):
        """Create an eventlog ZConfig configuration and patch it onto the
        global config, so it's present when ftw.structlog attempts to read it
        to derive its own logfile path from the eventlog's logfile path.
        """
        schema = ZConfig.loadSchemaFile(StringIO("""
            <schema>
              <import package='ZConfig.components.logger'/>
              <section type='eventlog' name='*' attribute='eventlog'/>
            </schema>
        """))

        fn = self.mktemp()
        eventlog_conf, handler = ZConfig.loadConfigFile(schema, StringIO("""
            <eventlog>
              <logfile>
                path %s
                level debug
              </logfile>
            </eventlog>
        """ % fn))

        assert eventlog_conf.eventlog is not None
        getConfiguration().eventlog = eventlog_conf.eventlog

    def remove_eventlog(self):
        conf = getConfiguration()
        del conf.eventlog

    def setUpZope(self, app, configurationContext):
        # Set up the eventlog config before ftw.structlog.logger gets imported
        self.setup_eventlog()

        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '  <include package="plone.rest" />'
            '  <include package="ftw.structlog.demo" />'
            '</configure>',
            context=configurationContext)

    def setUpPloneSite(self, portal):
        setRoles(portal, TEST_USER_ID, ['Manager'])

    def tearDownZope(self, app):
        self.remove_eventlog()

    def testTearDown(self):
        # Isolation: truncate ftw.structlog's logfile after each test
        log_path = get_log_path()
        if log_path and os.path.isfile(log_path):
            with open(log_path, 'w') as f:
                f.truncate()


class StructLogFluentLayer(PloneSandboxLayer):

    def setUpZope(self, app, configurationContext):
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '  <include package="plone.rest" />'
            '  <include package="ftw.structlog.demo" />'
            '</configure>',
            context=configurationContext)

    def setUpPloneSite(self, portal):
        setRoles(portal, TEST_USER_ID, ['Manager'])

    def setUp(self):
        os.environ['FLUENT_HOST'] = 'localhost'
        setup_logger()
        super(StructLogFluentLayer, self).setUp()

    def tearDown(self):
        os.environ.pop('FLUENT_HOST', None)

        # Remove any log handlers that were set up
        logger = logging.getLogger('ftw.structlog')
        map(logger.removeHandler, logger.handlers)
        super(StructLogFluentLayer, self).tearDown()


STRUCTLOG_FIXTURE = StructLogLayer()
STRUCTLOG_FUNCTIONAL_ZSERVER = FunctionalTesting(
    bases=(z2.ZSERVER_FIXTURE,
           REQUESTS_BROWSER_FIXTURE,
           STRUCTLOG_FIXTURE),
    name="ftw.structlog:functional:zserver")


STRUCTLOG_FLUENT_FIXTURE = StructLogFluentLayer()
STRUCTLOG_FUNCTIONAL_FLUENT = FunctionalTesting(
    bases=(z2.ZSERVER_FIXTURE,
           REQUESTS_BROWSER_FIXTURE,
           STRUCTLOG_FLUENT_FIXTURE),
    name="ftw.structlog:functional:fluent")
