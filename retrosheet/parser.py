# encoding: utf-8

import pandas as pd
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import logging
import datetime

from .event import Event, Event1
from .helpers import progress
from .version import __version__


class Parser(object):
    """docstring for Parser."""

    endpoint = 'https://www.retrosheet.org/events/'
    extension = '.zip'

    def __init__(self):
        #self.endpoint =
        #self.extension = '.zip'
        self.errors = []
        self.info = pd.DataFrame()
        self.starting = pd.DataFrame()
        self.plays = pd.DataFrame()
        self.er = pd.DataFrame()
        self.subs = pd.DataFrame()
        self.comments = pd.DataFrame()
        self.rosters = pd.DataFrame()
        self.teams = pd.DataFrame()
        self.metadata = pd.DataFrame()


    def _pitch_count(self, string, current_count):
        """
        For now it is including pickoffs
        """
        #simplest idea:
        clean_pitches = string.replace('>','').replace('+','').replace('*','').replace('??','')
        splits = clean_pitches.split('.') #results in a list
        count = current_count + len(splits[len(splits)-1])

        return count


    def parse_file(self, year):

        """
        Will parse the file respective for one year.
        - It will first look for the file in current directory
        - Else, it will take from the web (without making a copy)
        """

        event = Event()
        filename = '{0}eve{1}'.format(year, self.extension)

        try: #the files locally:
            zipfile = ZipFile(filename)
            self.log.debug("Found locally")
        except: #take from the web
            resp = urlopen(self.endpoint + filename)
            zipfile = ZipFile(BytesIO(resp.read()))
            self.log.debug("Donwloading from the web")

        infos, starting, plays, er, subs, comments, rosters, teams, metadata = ([] for i in range(9))

        for file in zipfile.namelist():

            metadata.append([file, datetime.datetime.now(), __version__])

            if file[:4] == 'TEAM':

                for row in zipfile.open(file).readlines():
                    row = row.decode("utf-8")
                    team_piece = []
                    for i in range(4): team_piece.append(row.rstrip('\n').split(',')[i].replace('\r',''))
                    teams.append([year]+team_piece)

            elif file[-3:] == 'ROS': #roster file

                for row in zipfile.open(file, 'r').readlines():
                    row = row.decode("utf-8")
                    roster_piece = []
                    for i in range(7): roster_piece.append(row.rstrip('\n').split(',')[i].replace('\r',''))
                    rosters.append([year]+roster_piece)

            else: #event file
                order, game_id, version, runs = (0 for i in range(4))
                inning = '1'
                team = '0'

                file_lines = zipfile.open(file, 'r').readlines()
                for loop, row in enumerate(file_lines):

                    row = row.decode("utf-8")
                    row_type = row.rstrip('\n').split(',')[0]

                    if row_type == 'id':

                        #initialize variables
                        order = 0
                        game_id = row.rstrip('\n').split(',')[1].strip('\r')
                        event.play = {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 3, 'run': 0}
                        home_team_score = 0
                        away_team_score = 0

                        infos.append([game_id, '__version__', __version__]) # parsing version
                        infos.append([game_id, 'file', file])               # file name

                    if row_type == 'version':
                        version = row.rstrip('\n').split(',')[1].strip('\r')

                    if row_type == 'info':
                        var = row.rstrip('\n').split(',')[1]
                        value = row.rstrip('\n').split(',')[2].replace('\r','').replace('"','')
                        value = None if value == 'unknown' else value
                        value = None if value == 0 and var == 'temp' else value
                        value = None if value == -1 and var == 'windspeed' else value

                        infos.append([game_id, var, value])

                    if row_type == 'start':
                        #starting pitchers
                        if row.rstrip('\n').split(',')[5].strip('\r') == '1':
                            if row.rstrip('\n').split(',')[3] == '1':
                                home_pitcher_id = row.rstrip('\n').split(',')[1]
                                home_pitch_count = 0
                            else: #away pitcher
                                away_pitcher_id = row.rstrip('\n').split(',')[1]
                                away_pitch_count = 0

                        start_piece = []
                        for i in range(1,6,1): start_piece.append(row.rstrip('\n').split(',')[i].replace('"','').replace('\r',''))
                        '''
                        start_piece = [
                            row.rstrip('\n').split(',')[1],
                            row.rstrip('\n').split(',')[2].strip('"'),
                            row.rstrip('\n').split(',')[3],
                            row.rstrip('\n').split(',')[4],
                            row.rstrip('\n').split(',')[5].strip('\r')
                        ]
                        '''
                        starting.append([game_id, version]+start_piece)

                    if row_type == 'play':

                        if team != row.rstrip('\n').split(',')[2]: #if previous team != current team
                            runs = 0
                            if not row.rstrip('\n').split(',')[2] == '0' and not row.rstrip('\n').split(',')[1] == '1': #if not first obs
                                #assert (event.play['out'] == 3),"Game: {3} Inning {0} team {4} ended with {1} outs [{2}]".format(inning,event.play['out'], event.str, game_id, team)
                                if event.play['out'] != 3:
                                    self.errors.append("Game: {3} Inning {0} team {4} ended with {1} outs [{2}]".format(inning,event.play['out'], event.str, game_id, team))
                                    event.play['out'] = 0


                        event.str = row.rstrip('\n').split(',')[6].strip('\r')
                        event.decipher()

                        if row.rstrip('\n').split(',')[2] == '0': #the opposite team is pitching
                            pitcher_id = home_pitcher_id
                            home_pitch_count = self._pitch_count(row.rstrip('\n').split(',')[5], home_pitch_count)
                            pitch_count = home_pitch_count
                            away_team_score = away_team_score + event.play['run'] - runs


                        elif row.rstrip('\n').split(',')[2] == '1': #away
                            pitcher_id = away_pitcher_id
                            away_pitch_count = self._pitch_count(row.rstrip('\n').split(',')[5], away_pitch_count)
                            pitch_count = away_pitch_count
                            home_team_score = home_team_score + event.play['run'] - runs


                        inning = row.rstrip('\n').split(',')[1]
                        team = row.rstrip('\n').split(',')[2]
                        runs = event.play['run']


                        play_piece = [
                            inning, team, pitcher_id, pitch_count,
                            row.rstrip('\n').split(',')[3],
                            row.rstrip('\n').split(',')[4],
                            row.rstrip('\n').split(',')[5],
                            row.rstrip('\n').split(',')[6].strip('\r'),
                            event.play['B'],
                            event.play['1'],
                            event.play['2'],
                            event.play['3'],
                            event.play['H'],
                            event.play['run'],
                            event.play['out'],
                            away_team_score,
                            home_team_score
                        ]
                        plays.append([order, game_id, version] + play_piece)

                        order += 1

                    if row_type == 'sub':
                        if row.rstrip('\n').split(',')[5].strip('\r') == '1':
                            if row.rstrip('\n').split(',')[3] == '1':
                                home_pitcher_id = row.rstrip('\n').split(',')[1]
                                #print ('sub: home pitcher: ', home_pitcher_id)
                                home_pitch_count = 0
                            else: #away pitcher
                                away_pitcher_id = row.rstrip('\n').split(',')[1]
                                #print ('sub: away pitcher: ', away_pitcher_id)
                                away_pitch_count = 0
                        sub_piece = [
                            row.rstrip('\n').split(',')[1],
                            row.rstrip('\n').split(',')[2].strip('"'),
                            row.rstrip('\n').split(',')[3],
                            row.rstrip('\n').split(',')[4],
                            row.rstrip('\n').split(',')[5].strip('\r')
                        ]
                        subs.append([order, game_id, version] + sub_piece)
                        order += 1

                    if row_type == 'com': #comments
                        com_piece = [
                            row.rstrip('\n').split('"')[1]
                        ]
                        comments.append([order, game_id, version] + com_piece)

                    if row_type == 'data':

                        #add info of game that just finished #check
                        infos.append([game_id, 'hometeam_score', home_team_score])
                        infos.append([game_id, 'awayteam_score', away_team_score])

                        data_piece = [
                            row.rstrip('\n').split(',')[1],
                            row.rstrip('\n').split(',')[2],
                            row.rstrip('\n').split(',')[3].strip('\r')
                        ]
                        er.append([game_id, version] + data_piece)

        rosters_df = pd.DataFrame(rosters, columns = ['year','player_id','last_name','first_name','batting_hand','throwing_hand','team_abbr_1','position'])
        teams_df = pd.DataFrame(teams, columns=['year','team_abbr','league','city','name'])


        info = pd.DataFrame(infos, columns = ['game_id','var','value'])
        games = info[~info.duplicated(subset=['game_id','var'], keep='last')].pivot('game_id','var','value').reset_index()
        #self.log.warning('{0}: Error on pivoting games'.format(year))
        #games = pd.DataFrame()

        starting_df = pd.DataFrame(starting, columns = ['game_id','version','player_id','player_name','home_team','batting_position','fielding_position'])
        subs_df = pd.DataFrame(subs, columns = ['order','game_id','version', 'player_id','player_name','home_team','batting_position','position'])
        plays_df = pd.DataFrame(plays, columns = [
            'order','game_id','version','inning','home_team','pitcher_id','pitch_count','batter_id','count_on_batter','pitches','play',
            'B','1','2','3','H','run','out','away_score','home_score'
        ])
        comments_df = pd.DataFrame(comments, columns = ['order','game_id','version','comment'])
        er_df = pd.DataFrame(er, columns = ['game_id','version','earned_run','player_id','variable'])
        metadata_df = pd.DataFrame(metadata, columns = ['file', 'datetime', 'version'])

        return games ,starting_df , plays_df, er_df, subs_df, comments_df, rosters_df, teams_df, metadata_df


    def get_data(self, yearFrom='2017', yearTo=None):

        if yearTo is None:
            yearTo = yearFrom

        self.log.warning('Parsing Files. Looking locally or downloading from retrosheet.org ...')

        for count, year in enumerate(range(yearFrom,yearTo+1,1), 0): #+1 for inclusive

            total = yearTo-yearFrom+1
            progress(count, total, status=year)

            info_temp, starting_temp, plays_temp, er_temp, subs_temp, comments_temp, rosters_temp, teams_temp, meta = self.parse_file(year)

            self.info = self.info.append(info_temp)
            self.starting = self.starting.append(starting_temp)
            self.plays = self.plays.append(plays_temp)
            self.er = self.er.append(er_temp)
            self.subs = self.subs.append(subs_temp)
            self.comments = self.comments.append(comments_temp)
            self.rosters = self.rosters.append(rosters_temp)
            self.teams = self.teams.append(teams_temp)
            self.metadata = self.metadata.append(meta)

        progress(100,100, status="Files Parsed")
        self.log.warning(self.errors)
        self.log.warning('Total errors: {0}'.format(len(self.errors)))

        return True#info, starting, plays, er, subs, comments, rosters, teams


    def save_csv(self, path=''):
        self.log.warning('Saving files to csv ({0}) ...'.format(path))

        self.info.to_csv('{0}info.csv'.format(path), index=False)
        self.starting.to_csv('{0}starting.csv'.format(path), index=False)
        self.plays.to_csv('{0}plays.csv'.format(path), index=False)
        self.er.to_csv('{0}er.csv'.format(path), index=False)
        self.subs.to_csv('{0}subs.csv'.format(path), index=False)
        self.comments.to_csv('{0}comments.csv'.format(path), index=False)
        self.rosters.to_csv('{0}rosters.csv'.format(path), index=False)
        self.teams.to_csv('{0}teams.csv'.format(path), index=False)
        self.metadata.to_csv('{0}metadata.csv'.format(path), index=False)

        self.log.warning('Saved ...')



class Retrosheet(Event1, Parser):

    """A python object to parse retrosheet data"""

    def __init__(self):
        Event1.__init__(self)
        Parser.__init__(self)
