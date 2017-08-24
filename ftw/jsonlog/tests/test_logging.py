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

    @browsing
    def test_logs_request_methods(self, browser):
        browser.login()

        browser.open(view='@@ping')
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(u'GET', log_entry['method'])

        browser.open(view='@@ping', method='POST')
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(u'POST', log_entry['method'])

        # TODO: Test more HTTP methods using plone.rest

    @browsing
    def test_logs_url(self, browser):
        browser.login()

        browser.open(view='@@ping')
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(
            u'http://localhost:55001/plone/@@ping',
            log_entry['url'])

    @browsing
    def test_logs_url_with_query_string(self, browser):
        browser.login()

        browser.open(view='@@ping?foo=bar')
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(
            u'http://localhost:55001/plone/@@ping?foo=bar',
            log_entry['url'])

    @browsing
    def test_logs_reponse_status(self, browser):
        browser.login()
        browser.raise_http_errors = False

        browser.open(view='@@ping')
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(200, log_entry['status'])

        browser.open(view='@@internal-server-error')
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(500, log_entry['status'])

        # TODO: Ask jone whether we can actually simulate a 401 here
        # TODO: Test 30x (redirects). Needs a change in ftw.testbrowser

        browser.open(view='@@doesnt-exist')
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(404, log_entry['status'])

    @browsing
    def test_logs_referer(self, browser):
        browser.login()

        # First request, no referer
        browser.open(self.portal)
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(None, log_entry['referer'])

        # Send referer with second request
        browser.open(view='@@ping', referer=True)
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(
            u'http://localhost:55001/plone',
            log_entry['referer'])

    @browsing
    def test_logs_user_agent(self, browser):
        browser.login()

        # Default user agent from requests module
        browser.open(self.portal)
        log_entry = self.get_log_entries()[-1]
        self.assertTrue(log_entry['user_agent'].startswith('python-requests'))

        # Custom user agent
        browser.open(self.portal, headers={'User-Agent': 'foobar/3.1415'})
        log_entry = self.get_log_entries()[-1]
        self.assertEquals('foobar/3.1415', log_entry['user_agent'])
