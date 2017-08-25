from App.config import getConfiguration
from logging import FileHandler
from logging import getLogger
import logging


logger = getLogger('ftw.jsonlog')


def setup_logger():
    if not logger.handlers:
        path = get_logfile_path()
        handler = FileHandler(path)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def get_logfile_path():
    """Determine the path for our JSON log.

    This will be derived from Zope2's EventLog location, in order to not
    have to figure out the path to var/log/ and the instance name ourselves.
    """
    zconf = getConfiguration()
    handler_factories = zconf.eventlog.handler_factories
    eventlog_path = handler_factories[0].section.path
    assert eventlog_path.endswith('.log')
    path = eventlog_path.replace('.log', '-json.log')
    return path


setup_logger()
