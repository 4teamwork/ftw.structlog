from datetime import datetime
from ftw.jsonlog.tests import FunctionalTestCase
from ftw.testbrowser import browsing
from ftw.testing import freeze
from operator import itemgetter
from plone.app.testing import TEST_USER_NAME


class TestLogging(FunctionalTestCase):

    @browsing
    def test_logs_basic_request_infos(self, browser):
        browser.login()
        with freeze(datetime(2017, 7, 29, 12, 30, 58, 750)):
            browser.open(self.portal)

        log_entry = self.get_log_entries()[-1]

        self.assertEquals(
            [u'status', u'url', u'timestamp', u'bytes', u'host',
             u'referer', u'user', u'duration', u'method', u'user_agent'],
            log_entry.keys())

    @browsing
    def test_logs_multiple_requests(self, browser):
        browser.login()
        with freeze(datetime(2017, 7, 29, 12, 30, 58, 750)) as clock:
            browser.open(self.portal)
            clock.forward(minutes=5)
            browser.open(self.portal)

        log_entries = self.get_log_entries()

        self.assertEquals(2, len(log_entries))
        self.assertEquals(
            [u'2017-07-29T12:30:58.000750', u'2017-07-29T12:35:58.000750'],
            map(itemgetter('timestamp'), log_entries))

    @browsing
    def test_logs_username_for_authenticated_user(self, browser):
        browser.login()
        browser.open(self.portal)

        log_entry = self.get_log_entries()[0]
        self.assertEquals(TEST_USER_NAME, log_entry['user'])

    @browsing
    def test_logs_username_for_anonymous(self, browser):
        browser.open(self.portal)

        log_entry = self.get_log_entries()[0]
        self.assertEquals(u'Anonymous User', log_entry['user'])
