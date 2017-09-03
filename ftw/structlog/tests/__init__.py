from ftw.structlog.testing import get_log_path
from ftw.structlog.testing import STRUCTLOG_FUNCTIONAL_ZSERVER
from unittest2 import TestCase
import json
import os


class FunctionalTestCase(TestCase):

    layer = STRUCTLOG_FUNCTIONAL_ZSERVER

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

    def get_log_entries(self):
        log_path = get_log_path()
        with open(log_path) as log:
            entries = map(json.loads, log.readlines())
        return entries

    @property
    def zserver_port(self):
        return str(os.environ.get('ZSERVER_PORT', 55001))
