import os
import json
import logging.config


from .event import Event, Event1
from .parser import Retrosheet
from .version import __version__


def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):

    """Setup logging configuration
    """

    path = default_path
    value = os.getenv(env_key, None)

    if value:
        path = value

    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)

        requests_log = logging.getLogger("requests")
        requests_log.setLevel(logging.WARNING)

    else:
        logging.basicConfig(level=default_level)


setup_logging()
