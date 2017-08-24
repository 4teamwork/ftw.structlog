from ftw.jsonlog.testing import get_log_path
from ftw.jsonlog.testing import JSONLOG_FUNCTIONAL_ZSERVER
from unittest2 import TestCase
import json


class FunctionalTestCase(TestCase):

    layer = JSONLOG_FUNCTIONAL_ZSERVER

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

    def get_log_entries(self):
        log_path = get_log_path()
        with open(log_path) as log:
            entries = map(json.loads, log.readlines())
        return entries
