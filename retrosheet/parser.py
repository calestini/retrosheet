# encoding: utf-8

from .event import event
from .game import parse_files
from .version import __version__


class Retrosheet(event, parse_files):

    """A python object to parse retrosheet data"""

    def __init__(self):
        self.__version__ = __version__
        event.__init__(self)
        parse_files.__init__(self)
