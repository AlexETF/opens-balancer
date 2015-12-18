import logging
import sys
import matplotlib
from config import config, credentials
from logger import log_parser
from exceptions import KeyboardInterrupt

from services.auth_service import AuthService

LOG_TAGS = config.log_tags;
LOG_SEPARATOR = config.log_tag_separator
LOG_DIR = config.log_directory

def setup_logging(log_filename):
    """ Metoda za inicijalizaciju log fajla u koji ce biti upisan parsirani sadrzaj """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    log_filename = LOG_DIR + "parsed-" + log_filename
    handler = logging.FileHandler(log_filename, mode = 'w')
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def main():

    try:
        if len(sys.argv) < 2:
            print('Unesite samo naziv log fajla iz %s direktorijuma' % LOG_DIR)
            return

        LOG_FILENAME = sys.argv[1]
        logger =  setup_logging(LOG_FILENAME)
        parser = log_parser.LogParser(logger)
        parser.parse_log(LOG_FILENAME)
        parser.show_graphs()
    except Exception as e:
        print e


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('EXIT TASK - CTRL + C Pressed')
    print('Izlaz')
