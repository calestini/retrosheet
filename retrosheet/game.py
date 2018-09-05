# encoding: utf-8

import logging
import re
from io import BytesIO
from zipfile import ZipFile
from collections import OrderedDict
import pandas as pd
from urllib.request import urlopen
import os.path

from .helpers import pitch_count, progress, game_state
from .version import __version__
from .event import  event


class parse_row(object):
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


class parse_game(parse_row):

    """"Object for each baseball game, subclass.
    - Data is expected to be sequentially passed (Retrosheet format)
    - When this class is initialized, it restarts all stats for the game
    """

    def __init__(self, id=''):
        self.log = logging.getLogger(__name__) #initialize logging
        parse_row.__init__(self)
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
            'starting_lineup':{'1': {}, '0': {}}, #static for each game
            'playing_lineup':{'1': {}, '0': {}}, #dynamic, based on subs
            'info': [], #'start': [],
            'play_data': [],
            'play_player': [], #pitching_id | batter_id | player_id | event | value |
            #'sub': [],
            'com': [],
            'data': [],
            'stats': {'pitching':[], 'batting':[], 'fielding': [], 'running':[]}
        }
        self.event = event()
        self.event.base = {'B': None,'1': None,'2': None,'3': None,'H': []}
        self.event.advances =  {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 3, 'run': 0}


    def parse_start(self, start_sub = 'start'):
        """ This will happen before the game starts"""
        fielding_position = self.row_values[5]
        player_id = self.row_values[1]
        home_away = self.row_values[-3][-1] #some entires are '01'

        try:
            self.current_pitcher[home_away] = player_id if fielding_position == '1' else self.current_pitcher[home_away]
            self.pitch_count[home_away] = 0 if fielding_position == '1' else self.pitch_count[home_away]
        except:
            self.log.debug('Something wrong with {0} home_away pitcher in {1}, {2}'.format(self.game['id'], start_sub, self.row_values))

        self.game['playing_lineup'][home_away][fielding_position] = player_id

        if start_sub == 'start':
            self.game['starting_lineup'][home_away][fielding_position] = player_id


    def parse_play(self):
        """
        -----------------------------------------------------------------------------------------
        field format: "play | inning | home_away | player_id | count on batter | pitches | play "|
        index counts:   0        1          2          3              4             5       6    |
        ------------------------------------------------------------------------------------------
        """

        self.event.str = self.row_values[6] #pass string to parse values

        if self.current_team != self.row_values[2]:
            self.score[self.current_team] += self.event.advances['run']
            self.event.base = {'B': None,'1': None,'2': None,'3': None, 'H': []} #players on base

            if self.event.advances['out'] != 3: #catching errors
                self.log.warning('INNING NO 3RD OUT:\tGame: {0}\tteam: {1}\tinning{2}\tout: {3}'.format(self.game['id'], self.current_team, self.current_inning, self.event.advances['out']))

        self.event.advances={'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0,'run': 0} if self.event.advances['out'] >= 3 else self.event.advances

        self.event.base['B'] = self.row_values[3] #current at bat
        base_before_play = self.event.base.copy()

        pre_event = self.event.advances.copy()
        self.event.decipher()
        post_event = self.event.advances.copy()
        this_play_runs = post_event['run'] - pre_event['run']
        this_play_outs = post_event['out'] - pre_event['out']
        pre_state, post_state = game_state(pre_event, post_event)

        if post_state == 25:
            states = [25,26,27,28]
            post_state = states[this_play_runs]


        pitcher_home_away = '1' if self.row_values[2] == '0' else '0' #remember picher is defense
        pitch_string = self.row_values[3]


        self.pitch_count[pitcher_home_away] = pitch_count(self.row_values[5], self.pitch_count[pitcher_home_away])
        self.current_inning = self.row_values[1]
        self.current_team = self.row_values[2] if self.row_values[2] in ['0','1'] else self.current_team

        if self.event.str != 'NP': #only append if plays happened (skip subs(NP) on play file)
            self.game['play_data'].append({
                'game_id': self.game['id'],
                'order': self.location,
                'pitcher': self.current_pitcher[pitcher_home_away],
                'pitch_count': self.pitch_count[pitcher_home_away],
                'inning': self.current_inning,
                'team': self.current_team,
                'player_id': self.row_values[3],
                'count_on_batter': self.row_values[4],
                'pitch_str': self.row_values[5],
                'play_str': self.row_values[6],
                'B': self.event.advances['B'],
                '1': self.event.advances['1'],
                '2': self.event.advances['2'],
                '3': self.event.advances['3'],
                'H': self.event.advances['H'],
                'run': self.event.advances['run'],
                'out': self.event.advances['out'],
                'on-B': self.event.base['B'],
                'on-1': self.event.base['1'],
                'on-2': self.event.base['2'],
                'on-3': self.event.base['3'],
                'on-H': self.event.base['H'],
                'hometeam_score': self.score['1'],
                'awayteam_score': self.score['0'],
                'trajectory': self.event.modifiers['trajectory'],
                'passes':  self.event.modifiers['passes'],
                'location':  self.event.modifiers['location'],
                'pre_state': pre_state,
                'post_state': post_state,
                'play_runs': this_play_runs,
                'play_outs': this_play_outs
            })


            #import stats for the play
            #batting
            for bat_stat in self.event.stats['batting']:
                bat_stat[1] = self.row_values[3]
                self.game['stats']['batting'].append([self.game['id'], self.location] + bat_stat)

            #pitching
            for pit_stat in self.event.stats['pitching']:
                pit_stat[1] = self.current_pitcher[pitcher_home_away]
                self.game['stats']['pitching'].append([self.game['id'], self.location] + pit_stat)

            #running -- > need to track player together with base
            for run_stat in self.event.stats['running']:
                run_stat.append(base_before_play[run_stat[1]])#bfrom
                self.game['stats']['running'].append([self.game['id'], self.location] + run_stat)


            #fielding --> use current positions
            fld_home_away = '1' if self.current_team == '0' else '0' #defense is the opposite team
            for fld_stat in self.event.stats['fielding']:
                try:
                    fld_stat[1] = self.game['playing_lineup'][fld_home_away][fld_stat[1]]
                except:
                    self.log.debug(fld_stat)
                self.game['stats']['fielding'].append([self.game['id'], self.location] + fld_stat)

        self.location += 1


    def parse_com(self):
        self.game['com'].append([self.game['id'], self.location] + self.row_data)


    def parse_event(self, row_str):
        self.row_str = row_str
        self.read_row()
        if self.row_id == 'id' or self.row_id == 'version':
            self.game[self.row_id] = self.row_data[0]
            self.has_started = True
        elif self.row_id == 'info':
            self.game[self.row_id].append([self.game['id'],self.row_values[1], self.row_values[2]])
        elif self.row_id == 'data':
            self.has_finished=True
            self.game['meta']['events'] = self.location + 1 #0 index
            if not self.game['data']:
                self.game['info'].append([self.game['id'], 'hometeam_score', self.score['1']])
                self.game['info'].append([self.game['id'], 'awayteam_score', self.score['0']])
            self.game[self.row_id].append([self.game['id'], self.game['meta']['events']]+self.row_data)
        else:
            self.parse_start(self.row_id) if self.row_id in ['start','sub'] else None
            self.parse_play() if self.row_id == 'play' else None
            self.parse_com() if self.row_id == 'com' else None


class parse_games(object):
    """
    """
    def __init__(self):
        self.log = logging.getLogger(__name__) #initialize logging
        self.file = None
        self.game_list = []
        self.zipfile = None


    def get_games(self):
        game = parse_game() #files in 1991 start with something other than id
        for loop, row in enumerate(self.zipfile.open(self.file).readlines()):
            if row.decode("utf-8").rstrip('\n').split(',')[0] == 'id':
                game_id = row.decode("utf-8").rstrip('\n').split(',')[1].rstrip('\r')
                #start new game
                self.game_list.append(game.game) if loop > 0 else None
                game = parse_game(game_id)
            else:
                game.parse_event(row)


    def debug_game(self, game_id):
        diamond = '''Play: {2}, Inning: {0}, Team: {1} \n|---------[ {5} ]-----------|\n|-------------------------|\n|----[ {6} ]------[ {4} ]-----|\n|-------------------------|\n|------[ {7} ]--[ {3} ]-------|\n|-------------------------|\nRuns: {8}\tOuts: {9}\n'''

        for game in self.game_list:
            if game['id'] == game_id:
                for play in game['play_data']:
                    print (diamond.format(
                        play['inning'], play['team'], play['play_str'],
                        play['B'],
                        play['1'],
                        play['2'],
                        play['3'],
                        play['H'],
                        play['run'],
                        play['out']
                    ))


class parse_files(parse_games):

    endpoint = 'https://www.retrosheet.org/events/'
    extension = '.zip'

    def __init__(self):
        parse_games.__init__(self)
        self.log = logging.getLogger(__name__)
        self.teams_list = []
        self.rosters_list = []

    def read_files(self):
        try: #the files locally:
            zipfile = ZipFile(self.filename)
            #self.log.debug("Found locally")
        except: #take from the web
            resp = urlopen(self.endpoint + self.filename)
            zipfile = ZipFile(BytesIO(resp.read()))
            #self.log.debug("Donwloading from the web")

        self.zipfile = zipfile

        teams = []
        rosters = []

        for file in self.zipfile.namelist():
            if file[-3:] in ['EVA','EVN']:
                self.file = file
                self.get_games()

            elif file[:4] == 'TEAM':
                year = file[4:8]
                for row in zipfile.open(file).readlines():
                    row = row.decode("utf-8")
                    team_piece = []
                    for i in range(4): team_piece.append(row.rstrip('\n').split(',')[i].replace('\r',''))
                    self.teams_list.append([year]+team_piece)

            elif file[-3:] == 'ROS': #roster file
                year = file[3:7]
                for row in zipfile.open(file, 'r').readlines():
                    row = row.decode("utf-8")
                    roster_piece = []
                    for i in range(7): roster_piece.append(row.rstrip('\n').split(',')[i].replace('\r',''))
                    self.rosters_list.append([year]+roster_piece)


    def get_data(self, yearFrom = None, yearTo = None):
        """
        """
        yearTo = yearTo if yearTo else '2017'
        yearFrom = yearFrom if yearFrom else yearTo

        for loop, year in enumerate(range(yearFrom, yearTo+1, 1)):
            progress(loop, (yearTo - yearFrom+1), status='Year: {0}'.format(year))
            self.log.debug('Getting data for {0}...'.format(year))
            self.filename = '{0}eve{1}'.format(year, self.extension)
            self.read_files()

        progress(1,1,'Completed {0}-{1}'.format(yearFrom, yearTo))
        return True


    def to_df(self):
        """
        """
        plays = []
        infos = []
        datas = []
        lineups = []
        battings = []
        fieldings = []
        pitchings = []
        runnings = []

        for loop, game in enumerate(self.game_list):
            plays += game['play_data']
            infos += game['info']
            datas += game['data']

            battings += game['stats']['batting']
            fieldings += game['stats']['fielding']
            pitchings += game['stats']['pitching']
            runnings += game['stats']['running']

            game['starting_lineup']['1']['game_id'] = game['id']
            game['starting_lineup']['1']['home_away'] = 'home'
            game['starting_lineup']['0']['game_id'] = game['id']
            game['starting_lineup']['0']['home_away'] = 'away'

            lineups.append(game['starting_lineup']['1'])
            lineups.append(game['starting_lineup']['0'])

        self.plays = pd.DataFrame(plays)
        self.info = pd.DataFrame(infos, columns = ['game_id', 'var', 'value'])
        #self.info = self.info[~self.info.duplicated(subset=['game_id','var'], keep='last')].pivot('game_id','var','value').reset_index()

        self.lineup = pd.DataFrame(lineups)
        self.fielding = pd.DataFrame(fieldings, columns = ['game_id','order','stat','player_id'])

        data_df = pd.DataFrame(datas, columns = ['game_id','order','stat','player_id','value'])
        self.pitching = pd.DataFrame(pitchings, columns = ['game_id','order','stat','player_id'])
        self.pitching['value'] = 1
        self.pitching = pd.concat([self.pitching, data_df], axis = 0)

        self.batting =  pd.DataFrame(battings, columns = ['game_id','order','stat','player_id'])
        self.running =  pd.DataFrame(runnings, columns = ['game_id','order','stat','bfrom','bto','player_id'])

        self.rosters = pd.DataFrame(self.rosters_list, columns = ['year','player_id','last_name','first_name','batting_hand','throwing_hand','team_abbr_1','position'])
        self.teams = pd.DataFrame(self.teams_list, columns=['year','team_abbr','league','city','name'])

        return True


    def save_csv(self, path_str='', append=True):
        """save dataframes to csv
            append = True for large downloads
        """
        if path_str:
            path_str + '/'  if path_str[-1] != '/' else path_str

        datasets = {
            'plays': self.plays,
            'info': self.info,
            'lineup': self.lineup,
            'fielding': self.fielding,
            'pitching': self.pitching,
            'batting': self.batting,
            'running': self.running,
            'rosters': self.rosters,
            'teams': self.teams,
        }

        for key, dataset in datasets.items():
            filename = path_str + key + '.csv'
            if not os.path.isfile(filename):
                dataset.to_csv(filename, mode='w', index=False, header=True)
            elif os.path.isfile(filename) and append==True:
                dataset.to_csv(filename, mode='a', index=False, header=False)
            else:
                dataset.to_csv(filename, mode='w', index=False, header=True)

        return True
