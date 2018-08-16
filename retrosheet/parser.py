# encoding: utf-8

import pandas as pd
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import sys
import logging


class Parser(object):

    """A python object to parse retrosheet data"""

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.endpoint = 'https://www.retrosheet.org/events/'
        self.extension = '.zip'

    def _progress(self, count, total, status=''):
        """
        Adapted from https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
        """
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)

        sys.stdout.write('[{0}] {1}{2} ... {3}\r'.format(bar, percents, '%', status))
        sys.stdout.flush()

    def _position_name(self, position_number):
        """
        """
        position_dic = {
            '1':'P',    #pitcher
            '2':'C',    #catcher
            '3':'1B',   #first baseman
            '4':'2B',   #second baseman
            '5':'3B',   #thrid baseman
            '6':'SS',   #shortstop
            '7':'LF',   #left fielder
            '8':'CF',   #center fielder
            '9':'RF',   #right fielder
            '10':'DH',  #designated hitter
            '11':'PH',  #pinch hitter
            '12':'PR',  #pinch runner
            }
        return position_dic[position_number]

    def _pitch_count(self, string, current_count):
        """
        For now it is including pickoffs
        """
        #simplest idea:
        clean_pitches = string.replace('>','').replace('+','').replace('*','').replace('??','')
        splits = clean_pitches.split('.') #results in a list
        count = current_count + len(splits[len(splits)-1])

        return count

    def _play_decipher(self, string):
        """understand each play from notation
        """
        R = 0#runs
        A = 0#assists - credited to every defensive player who fields or touches the ball
        O = 0#outs
        E = 0#error

        pass

    def parse_file(self, year):
        ########################################################################
        #ENDPOINT = 'https://www.retrosheet.org/events/'
        #EXTENSION = '.zip'
        ########################################################################
        """
        Will parse the file respective for one year.
        - It will first look for the file in current directory
        - Else, it will take from the web (without making a copy)
        """

        filename = '{0}eve{1}'.format(year, self.extension)

        try: #the files locally:
            zipfile = ZipFile(filename)
            self.log.debug("Found locally")
        except: #take from the web
            resp = urlopen(self.endpoint + filename)
            #print (year)
            zipfile = ZipFile(BytesIO(resp.read()))
            self.log.debug("Donwloading from the web")

        infos = []
        starting = []
        plays = []
        er = [] #earned runs
        subs = []
        comments = []
        rosters = []
        teams = []

        for file in zipfile.namelist():

            if file[:4] == 'TEAM':

                for row in zipfile.open(file).readlines():
                    row = row.decode("utf-8")

                    team_piece = [
                        row.rstrip('\n').split(',')[0],
                        row.rstrip('\n').split(',')[1],
                        row.rstrip('\n').split(',')[2],
                        row.rstrip('\n').split(',')[3].strip('\r')
                    ]

                    teams.append([year]+team_piece)

            elif file[-3:] == 'ROS': #roster file
                team_abbr = file[:3]

                for row in zipfile.open(file, 'r').readlines():
                    row = row.decode("utf-8")

                    roster_piece = [
                        row.rstrip('\n').split(',')[0],
                        row.rstrip('\n').split(',')[1],
                        row.rstrip('\n').split(',')[2],
                        row.rstrip('\n').split(',')[3],
                        row.rstrip('\n').split(',')[4],
                        row.rstrip('\n').split(',')[5],
                        row.rstrip('\n').split(',')[6].strip('\r')
                    ]

                    rosters.append([year, team_abbr]+roster_piece)

            else: #event file
                #print (file)
                order = 0
                game_id = 0
                version = 0
                for loop, row in enumerate(zipfile.open(file, 'r').readlines()):

                    row = row.decode("utf-8")
                    #rows.append(row.rstrip('\n'))
                    row_type = row.rstrip('\n').split(',')[0]
                    #print (row_type)

                    if row_type == 'id':
                        order = 0
                        game_id = row.rstrip('\n').split(',')[1].strip('\r')
                        #print ('\nGame:\t{0}'.format(game_id))
                        #ids.append(game_id)

                    if row_type == 'version':

                        version = row.rstrip('\n').split(',')[1].strip('\r')
                        #versions.append(version)

                    if row_type == 'info':
                        #if row.rstrip('\n').split(',')[1] != 'save':
                        info_piece = [
                            row.rstrip('\n').split(',')[1],
                            row.rstrip('\n').split(',')[2].strip('\r').strip('"').strip('"')
                        ]
                        infos.append([game_id]+ info_piece)

                    if row_type == 'start':
                        #it marks the starting players for a game
                        #first take pitcher id
                        if row.rstrip('\n').split(',')[5].strip('\r') == '1':
                            if row.rstrip('\n').split(',')[3] == '1':
                                home_pitcher_id = row.rstrip('\n').split(',')[1]
                                home_pitch_count = 0
                                #print ('home pitcher: ', home_pitcher_id)
                            else: #away pitcher
                                away_pitcher_id = row.rstrip('\n').split(',')[1]
                                away_pitch_count = 0
                                #print ('away pitcher: ', away_pitcher_id)

                        start_piece = [
                            row.rstrip('\n').split(',')[1],
                            row.rstrip('\n').split(',')[2].strip('"'),
                            row.rstrip('\n').split(',')[3],
                            row.rstrip('\n').split(',')[4],
                            row.rstrip('\n').split(',')[5].strip('\r')
                        ]
                        starting.append([game_id, version]+start_piece)

                    if row_type == 'play':
                        if row.rstrip('\n').split(',')[2] == '0': #the opposite team is pitching
                            pitcher_id = home_pitcher_id
                            #calculate new home pitch count
                            home_pitch_count = self._pitch_count(row.rstrip('\n').split(',')[5], home_pitch_count)
                            pitch_count = home_pitch_count
                        else: #away
                            pitcher_id = away_pitcher_id
                            #calculate new away pitch count
                            away_pitch_count = self._pitch_count(row.rstrip('\n').split(',')[5], away_pitch_count)
                            pitch_count = away_pitch_count

                        play_piece = [
                            row.rstrip('\n').split(',')[1],
                            row.rstrip('\n').split(',')[2],
                            pitcher_id,
                            pitch_count,
                            row.rstrip('\n').split(',')[3],
                            row.rstrip('\n').split(',')[4],
                            row.rstrip('\n').split(',')[5],
                            row.rstrip('\n').split(',')[6].strip('\r')
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
                        data_piece = [
                            row.rstrip('\n').split(',')[1],
                            row.rstrip('\n').split(',')[2],
                            row.rstrip('\n').split(',')[3].strip('\r')
                        ]
                        er.append([game_id, version] + data_piece)

        #dataframe for ids and versions. Information purposes only
        #ids_df = pd.DataFrame(ids, columns = ['game_id'])
        #versions_df = pd.DataFrame(versions, columns = ['version'])

        #rosters
        rosters_df = pd.DataFrame(rosters, columns = ['year','team_abbr','player_id','last_name','first_name','batting_hand','throwing_hand','team_abbr','position'])

        #teams
        teams_df = pd.DataFrame(teams, columns=['year','team_abbr','league','city','name'])

        #dataframe games with game info
        games = pd.DataFrame(infos, columns = ['game_id','var','value']).drop_duplicates()#\
            #.pivot('game_id','var','value').reset_index()

        #starting roster.
        starting_df = pd.DataFrame(starting, columns = ['game_id','version','player_id','player_name','home_team','batting_position','fielding_position'])

        #subs actions. It has the order, or when it happened, followed by the play df
        subs_df = pd.DataFrame(subs, columns = ['order','game_id','version', 'player_id','player_name','home_team','batting_position','position'])

        #play-by-play dataframe. Plays are not parsed yet.
        plays_df = pd.DataFrame(plays, columns = ['order','game_id','version','inning','home_team','pitcher_id','pitch_count','batter_id','count_on_batter','pitches','play'])

        #comments are not parsed.
        comments_df = pd.DataFrame(comments, columns = ['order','game_id','version','comment'])

        #earned runs for each pitcher.
        er_df = pd.DataFrame(er, columns = ['game_id','version','earned_run','player_id','variable'])

        return games ,starting_df , plays_df, er_df, subs_df, comments_df, rosters_df, teams_df#, ids_df, versions_df


    def parse_years(self, yearFrom, yearTo, save_to_csv=True):

        info = pd.DataFrame()
        starting = pd.DataFrame()
        plays = pd.DataFrame()
        er = pd.DataFrame()
        subs = pd.DataFrame()
        comments = pd.DataFrame()
        rosters = pd.DataFrame()
        teams = pd.DataFrame()

        self.log.warning('Downloading Files ...')
        for count, year in enumerate(range(yearFrom,yearTo+1,1), 0): #+1 for inclusive
            #print (yea)
            total = yearTo-yearFrom+1
            self._progress(count, total, status=year)

            info_temp, starting_temp, plays_temp, er_temp, subs_temp, comments_temp, rosters_temp, teams_temp = self.parse_file(year)

            info = info.append(info_temp)
            starting = starting.append(starting_temp)
            plays = plays.append(plays_temp)
            er = er.append(er_temp)
            subs = subs.append(subs_temp)
            comments = comments.append(comments_temp)
            rosters = rosters.append(rosters_temp)
            teams = teams.append(teams_temp)

        self._progress(100,100, status="Files Downloaded")

        if save_to_csv:
            self.log.warning('Saving files to csv ...')

            info.to_csv('info.csv', index=False)
            starting.to_csv('starting.csv', index=False)
            plays.to_csv('plays.csv', index=False)
            er.to_csv('er.csv', index=False)
            subs.to_csv('subs.csv', index=False)
            comments.to_csv('comments.csv', index=False)
            rosters.to_csv('rosters.csv', index=False)
            teams.to_csv('teams.csv', index=False)

            self.log.warning('Saved ...')

        return info, starting, plays, er, subs, comments, rosters, teams
