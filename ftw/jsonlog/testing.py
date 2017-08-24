from App.config import getConfiguration
from ftw.testbrowser import REQUESTS_BROWSER_FIXTURE
from logging import getLogger
from plone.app.testing import FunctionalTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from StringIO import StringIO
from zope.configuration import xmlconfig
import os
import tempfile
import ZConfig


def get_log_path():
    """Get filesystem path to ftw.jsonlog's logfile.
    """
    logger = getLogger('ftw.jsonlog')
    jsonlog_path = logger.handlers[0].stream.name
    return jsonlog_path


class JSONLogLayer(PloneSandboxLayer):

    def setUp(self):
        # Keep track of temporary files we create
        self._created_tempfiles = []
        super(JSONLogLayer, self).setUp()

    def tearDown(self):
        super(JSONLogLayer, self).tearDown()

        # Clean up all temporary files we created
        while self._created_tempfiles:
            os.unlink(self._created_tempfiles.pop())

    def mktemp(self):
        """Create a temporary file to use as the path for the eventlog.

        We don't actually care about the contents of this file, we just need
        it to get a valid writable path to pass to the eventlog config, so
        ftw.contentstats can derive its own logfile path from it.

        The filename mimics the instance eventlog's filename though, so that
        ftw.jsonlog can recognize the filename format and derive a filename
        with its own '-json.log' suffix.
        """
        fd, fn = tempfile.mkstemp(prefix='instance0-', suffix='.log')
        os.close(fd)
        self._created_tempfiles.append(fn)
        return fn

    def setup_eventlog(self):
        """Create an eventlog ZConfig configuration and patch it onto the
        global config, so it's present when ftw.jsonlog attempts to read it
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
        # Set up the eventlog config before ftw.jsonlog.logger gets imported
        self.setup_eventlog()

        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '</configure>',
            context=configurationContext)

    def tearDownZope(self, app):
        self.remove_eventlog()

    def testTearDown(self):
        # Isolation: truncate ftw.jsonlog's logfile after each test
        with open(get_log_path(), 'w') as f:
            f.truncate()


JSONLOG_FIXTURE = JSONLogLayer()
JSONLOG_FUNCTIONAL_ZSERVER = FunctionalTesting(
    bases=(z2.ZSERVER_FIXTURE,
           REQUESTS_BROWSER_FIXTURE,
           JSONLOG_FIXTURE),
    name="ftw.jsonlog:functional:zserver")
