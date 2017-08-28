from datetime import datetime
from ftw.jsonlog.tests import FunctionalTestCase
from ftw.testbrowser import browsing
from ftw.testing import freeze
from operator import itemgetter
from plone.app.testing import TEST_USER_NAME
from requests_toolbelt.adapters.source import SourceAddressAdapter
import sys
import unittest


class TestLogging(FunctionalTestCase):

    @browsing
    def test_logs_basic_request_infos(self, browser):
        browser.login()
        with freeze(datetime(2017, 7, 29, 12, 30, 58, 750)):
            browser.open(self.portal)

        log_entry = self.get_log_entries()[-1]

        self.assertItemsEqual(
            [u'status', u'url', u'timestamp', u'bytes', u'host', u'site',
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
    def test_logs_plone_site_id(self, browser):
        browser.open(self.portal)

        log_entry = self.get_log_entries()[0]
        self.assertEquals(u'plone', log_entry['site'])

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

        browser.open(view='@rest-endpoint', method='PUT',
                     headers={'Accept': 'application/json'})
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(u'PUT', log_entry['method'])

        browser.open(view='@rest-endpoint', method='PATCH',
                     headers={'Accept': 'application/json'})
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(u'PATCH', log_entry['method'])

        browser.open(view='@rest-endpoint', method='DELETE',
                     headers={'Accept': 'application/json'})
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(u'DELETE', log_entry['method'])

        browser.open(view='@rest-endpoint', method='HEAD',
                     headers={'Accept': 'application/json'})
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(u'HEAD', log_entry['method'])

    @browsing
    def test_logs_url(self, browser):
        browser.login()

        browser.open(view='@@ping')
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(
            u'http://localhost:%s/plone/@@ping' % self.zserver_port,
            log_entry['url'])

    @browsing
    def test_logs_url_with_query_string(self, browser):
        browser.login()

        browser.open(view='@@ping?foo=bar')
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(
            u'http://localhost:%s/plone/@@ping?foo=bar' % self.zserver_port,
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

        browser.open(view='@@unauthorized')
        log_entry = self.get_log_entries()[-1]
        self.assertEquals(401, log_entry['status'])

        browser.open(view='@@redirect')
        log_entry = self.get_log_entries()[-2]
        self.assertEquals(302, log_entry['status'])

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
            u'http://localhost:%s/plone' % self.zserver_port,
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

    @browsing
    def test_logs_timestamp(self, browser):
        browser.login()

        with freeze(datetime(2017, 7, 29, 12, 30, 58, 750)):
            browser.open(self.portal)

        log_entry = self.get_log_entries()[-1]
        self.assertEqual(u'2017-07-29T12:30:58.000750', log_entry['timestamp'])

    @browsing
    def test_logs_duration(self, browser):
        browser.login()
        browser.open(self.portal)

        log_entry = self.get_log_entries()[-1]
        self.assertIsInstance(log_entry['duration'], float)

    @browsing
    def test_logs_response_content_length_in_bytes(self, browser):
        browser.login()
        browser.open(self.portal, view='send-100-bytes')

        log_entry = self.get_log_entries()[-1]
        self.assertEquals(100, log_entry['bytes'])

    @browsing
    def test_logs_standard_source_address(self, browser):
        browser.login()

        # Standard source address
        browser.open(self.portal)
        log_entry = self.get_log_entries()[-1]
        self.assertEqual('127.0.0.1', log_entry['host'])

    # Mac OS rejects source addresses other than 127.0.0.1 from the loopback
    # interface with "[Errno 49] Can't assign requested address"
    @unittest.skipIf(sys.platform == 'darwin', "Can't test this on Mac OS")
    @browsing
    def test_logs_different_source_address(self, browser):
        source = SourceAddressAdapter('127.0.0.42')
        browser.get_driver().requests_session.mount('http://', source)

        browser.open('http://localhost:%s/plone' % self.zserver_port)
        log_entry = self.get_log_entries()[-1]
        self.assertEqual('127.0.0.42', log_entry['host'])
