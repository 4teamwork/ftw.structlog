from contextlib import contextmanager
from fluent.asynchandler import FluentHandler
from ftw.structlog.logger import setup_logger
from ftw.structlog.testing import env_var
from logging import FileHandler
from mock import patch
from StringIO import StringIO
from unittest2 import TestCase
import logging


class TestSetupLogger(TestCase):

    def testSetUp(self):
        logger = logging.getLogger('ftw.structlog')
        # If the functional tests are executed before these tests, the log handlers
        # are already there and no setup happens.
        map(logger.removeHandler, logger.handlers)

    def test_logs_errors_when_eventlog_is_missing(self):
        """
        When the event log is missing in the zope configuration, ftw.structlog
        noisily complains since it will result in missing log data.

        In test setups we sometimes do not have an eventlog configured and we do not
        care about ftw.structlog. In this situation we want to be able to mute the errors.
        This can be done with an environment variable.
        """

        with self.expect_log_output(
                "ftw.structlog: Couldn't find eventlog configuration in order to"
                " determine logfile location!\n"
                "ftw.structlog: No request logfile will be written!"):
            setup_logger()

        with self.expect_log_output(''):
            with env_var('FTW_STRUCTLOG_MUTE_SETUP_ERRORS', 'true'):
                setup_logger()

    @patch('ftw.structlog.logger.get_logfile_path')
    def test_sets_up_file_handler_by_default(self, mocked_logpath):
        mocked_logpath.return_value = '/tmp/logfile'
        logger = setup_logger()

        self.assertEqual(1, len(logger.handlers))
        handler = logger.handlers[0]
        self.assertIsInstance(handler, FileHandler)
        self.assertEqual('/tmp/logfile', handler.stream.name)

    @patch('ftw.structlog.logger.get_logfile_path')
    def test_sets_up_fluent_handler_if_envvar_set(self, mocked_logpath):
        # Mock the presence of a possible log file path in order to test that
        # even if one could be determined, setup_logger() *doesn't* set up
        # a FileHandler if FLUENT_HOST is set.
        mocked_logpath.return_value = '/tmp/logfile'

        logger = logging.getLogger('ftw.structlog')
        map(logger.removeHandler, logger.handlers)

        with env_var('FLUENT_HOST', 'localhost'):
            logger = setup_logger()

        self.assertEqual(1, len(logger.handlers))
        handler = logger.handlers[0]
        self.assertIsInstance(handler, FluentHandler)

    @contextmanager
    def expect_log_output(self, expected):
        with self.captured_log() as output:
            yield

        self.assertEqual(expected.strip(), output.getvalue().strip())

    @contextmanager
    def captured_log(self):
        output = StringIO()
        handler = logging.StreamHandler(output)
        logging.root.addHandler(handler)
        try:
            yield output
        finally:
            logging.root.removeHandler(handler)
