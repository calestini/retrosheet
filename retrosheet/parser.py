# encoding: utf-8

from .event import event
from .game import parse_files
from .version import __version__
import logging

class Retrosheet(event, parse_files):

    """A python object to parse retrosheet data"""

    def __init__(self):
        self.__version__ = __version__
        self.log = logging.getLogger(__name__)
        event.__init__(self)
        parse_files.__init__(self)


    def batch_parse(self, yearFrom = None, yearTo = None, batchsize=10):
        """
        """
        yearTo = yearTo if yearTo else '2017'
        yearFrom = yearFrom if yearFrom else yearTo

        if yearFrom < 1921 or yearTo > 2017 or yearTo < yearFrom:
            raise InvalidYearError('Invalid Years', (yearFrom, yearTo))

        batches = int((yearTo - yearFrom + 1)/batchsize)+1

        for loop, batch in enumerate(range(batches)):
            start_year = yearFrom if loop == 0 else end_year + 1

            end_year = start_year + batchsize-1 if (start_year + batchsize-1) <= yearTo else yearTo

            self.get_data(yearFrom=start_year, yearTo=end_year)
            self.to_df()
            self.save_csv(path_str='', append = True)

            #empty datasets for free-up memory
            self.file = None
            self.game_list = []
            self.zipfile = None
            self.teams_list = []
            self.rosters_list = []
            self.plays = None
            self.info = None
            self.lineup = None
            self.fielding = None
            self.pitching = None
            self.batting = None
            self.running = None
            self.rosters = None
            self.teams = None


class InvalidYearError(Exception):
    """ Exception that is raised when years are not within possible range
    """
    def __init__(self, error, years):
        self.log = logging.getLogger(__name__)
        self.log.debug("Invalid Year Passed: {0}-{1}".format(years[0], years[1]))
        super(InvalidYearError, self).__init__(years)
