# encoding: utf-8

import logging
import re
from io import BytesIO
from zipfile import ZipFile
from collections import OrderedDict

from .helpers import out_in_advance, advance_base, pitch_count
from .version import __version__
from .event import Event, Event1


class Parse_Row(object):
    """ Parse one single row
    - A row can return only one type of data (id, version, start, play, sub, com, data)
    """
    def __init__(self):
        self.log = logging.getLogger(__name__) #initialize logging
        self.row_str =''
        self.row_values = []
        self.row_results  = {}
        self.row_data = []
        self.row_id = []

    def _clean_row(self):
        self.row_str = self.row_str.decode("utf-8")
        self.row_values = self.row_str.rstrip('\n').split(',')
        self.row_values = [x.replace('\r','').replace('"','') for x in self.row_values]

    def read_row(self):
        self._clean_row()
        self.row_id = self.row_values[0] #string
        self.row_data = self.row_values[1:] #list


class Parse_Game(Parse_Row):
    """"Object for each baseball game, subclass.
    - Data is expected to be sequentially passed (Retrosheet format)
    - When this class is initialized, it restarts all stats for the game
    """

    def __init__(self, id=''):
        self.log = logging.getLogger(__name__) #initialize logging
        Parse_Row.__init__(self)
        self.location = 0
        self.has_started = False
        self.has_finished = False
        self.current_inning = '1' #starting of game
        self.current_team = '0'   #starting of game
        self.score = {'1':0,'0':0}
        self.current_pitcher = {'1':'','0':''} #1 for home, 0 for away
        self.pitch_count = {'1':0,'0':0} #1 for home, 0 for away
        self.game = {
            'meta': {'filename': '', '__version__': __version__, 'events':''},
            'id': id,
            'version': '',
            'starting_lineup':{'home': {}, 'away': {}}, #static for each game
            'playing_lineup':{'home': {}, 'away': {}}, #dynamic, based on subs
            'info': [], #'start': [],
            'play_raw': [],
            'play_player': [], #pitching_id | batter_id | player_id | event | value |
            'sub': [],
            'com': [],
            'data': [],
            'stats': {'pitching':[], 'batting':[], 'fielding': [], 'running':[]}
        }
        self.event = Event1()
        self.event.advances =  {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 3, 'run': 0}


    def parse_start(self, start_sub = 'start'):
        """ This will happen before the game starts"""
        fielding_position = self.row_values[5]
        player_id = self.row_values[1]
        home_away = self.row_values[3]

        self.current_pitcher[home_away] = player_id if fielding_position == '1' else self.current_pitcher[home_away]
        self.pitch_count[home_away] = 0 if fielding_position == '1' else self.pitch_count[home_away]

        if start_sub == 'start':
            if home_away == '1': #home team
                self.game['starting_lineup']['home'][fielding_position] = player_id
                self.game['playing_lineup']['home'][fielding_position] = player_id
            else: #away team
                self.game['starting_lineup']['away'][fielding_position] = player_id
                self.game['playing_lineup']['away'][fielding_position] = player_id
        else: #substitution
            #annotate pitcher statistics here
            if home_away == '1': #home
                self.game['playing_lineup']['home'][fielding_position] = player_id
            else: #away team
                self.game['playing_lineup']['away'][fielding_position] = player_id


    def parse_play(self):
        """
        -----------------------------------------------------------------------------------------
        field format: "play | inning | home_away | player_id | count on batter | pitches | play "|
        index counts:   0        1          2          3              4             5       6    |
        ------------------------------------------------------------------------------------------
        """
        self.event.str = self.row_values[6]

        #catching errors
        if self.current_team != self.row_values[2] and self.event.advances['out'] != 3:
            self.log.warning('INNING NO 3RD OUT:\tGame: {0}\tteam: {1}\tinning{2}\tout: {3}'.format(self.game['id'], self.current_team, self.current_inning, self.event.advances['out']))

        self.event.advances={'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0,'run': 0} if self.event.advances['out'] >= 3 else self.event.advances
        self.event.decipher()

        pitcher_home_away = '1' if self.row_values[2] == '0' else '0' #remember picher is defense
        pitch_string = self.row_values[3]
        self.pitch_count[pitcher_home_away] = pitch_count(self.row_values[5], self.pitch_count[pitcher_home_away])
        self.game['play_raw'].append(
            [
                self.location,
                self.current_pitcher[pitcher_home_away],
                self.pitch_count[pitcher_home_away],
            ] + self.row_data + [
                self.event.advances['B'],
                self.event.advances['1'],
                self.event.advances['2'],
                self.event.advances['3'],
                self.event.advances['H'],
                self.event.advances['run'],
                self.event.advances['out'],
            ])

        self.location += 1
        self.current_inning = self.row_values[1]
        self.current_team = self.row_values[2]
        pass

    def parse_com(self):
        self.game['com'].append([self.location] + self.row_data)

    def parse_event(self, row_str):
        self.row_str = row_str
        self.read_row()
        if self.row_id == 'id' or self.row_id == 'version':
            self.game[self.row_id] = self.row_data[0]
            self.has_started = True
        elif self.row_id == 'info':
            self.game[self.row_id].append(self.row_data)
        elif self.row_id == 'data':
            self.has_finished=True
            self.game['meta']['events'] = self.location + 1 #0 index
            if not self.game['data']:
                self.game['info'].append(['hometeam_score', self.score['1']])
                self.game['info'].append(['awayteam_score', self.score['0']])
            self.game[self.row_id].append(self.row_data)
        else:
            self.parse_start(self.row_id) if self.row_id in ['start','sub'] else None
            self.parse_play() if self.row_id == 'play' else None
            self.parse_com() if self.row_id == 'com' else None





class Parse_Games(object):
    def __init__(self):
        self.log = logging.getLogger(__name__) #initialize logging
        self.file = None
        self.game_list = []
        self.zipfile = None

    def get_games(self):

        for loop, row in enumerate(self.zipfile.open(self.file).readlines()):
            if row.decode("utf-8").rstrip('\n').split(',')[0] == 'id':
                game_id = row.decode("utf-8").rstrip('\n').split(',')[1].rstrip('\r')
                #start new game
                self.game_list.append(game.game) if loop > 0 else None
                game = Parse_Game(game_id)
            else:
                game.parse_event(row)


class Parse_Files(Parse_Games):

    endpoint = 'https://www.retrosheet.org/events/'
    extension = '.zip'

    def __init__(self, yearFrom = None, yearTo = None):
        Parse_Games.__init__(self)
        self.log = logging.getLogger(__name__)
        self.yearFrom = yearFrom
        self.yearTo = yearTo

    def read_files(self):
        try: #the files locally:
            zipfile = ZipFile(self.filename)
            self.log.debug("Found locally")
        except: #take from the web
            resp = urlopen(self.endpoint + self.filename)
            zipfile = ZipFile(BytesIO(resp.read()))
            self.log.debug("Donwloading from the web")

        self.zipfile = zipfile

        for file in self.zipfile.namelist():
            if file[-3:] in ['EVA','EVN']:
                self.file = file
                self.get_games()

    def get_data(self):
        for year in range(self.yearFrom, self.yearTo+1, 1):
            self.filename = '{0}eve{1}'.format(year, self.extension)
            self.read_files()
