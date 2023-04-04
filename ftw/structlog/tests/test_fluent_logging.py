from ftw.structlog.logger import setup_logger
from ftw.structlog.testing import clear_log_handlers
from ftw.structlog.testing import env_var
from ftw.structlog.testing import STRUCTLOG_FUNCTIONAL_FLUENT
from ftw.structlog.tests import FunctionalTestCase
from ftw.testbrowser import browsing
from mock import patch
import json


class TestFluentLogging(FunctionalTestCase):

    layer = STRUCTLOG_FUNCTIONAL_FLUENT

    def test_sets_up_tag_including_ns_for_fluent_handler(self):
        clear_log_handlers()

        with env_var('KUBERNETES_NAMESPACE', 'demo-example-org'):
            logger = setup_logger()
        handler = logger.handlers[0]
        self.assertEqual('demo-example-org-structlog-json.log', handler.tag)

    def test_sets_up_fallback_tag_for_fluent_handler(self):
        clear_log_handlers()

        logger = setup_logger()
        handler = logger.handlers[0]
        self.assertEqual('structlog-json.log', handler.tag)

    @browsing
    @patch('fluent.handler.FluentHandler.emit')
    def test_dispatches_to_fluent_handler(self, browser, mock_emit):
        setup_logger()
        browser.open(self.portal)

        self.assertEqual(1, mock_emit.call_count)
        log_record = mock_emit.call_args[0][0]

        self.assertDictContainsSubset({
            u'status': 200,
            u'client_ip': u'127.0.0.1',
            u'bytes': 8133,
            u'site': u'plone',
            u'host': u'127.0.0.1',
            u'referer': u'',
            u'user': u'Anonymous User',
            u'view': u'folder_listing',
            u'method': u'GET',
        }, json.loads(log_record.msg))
