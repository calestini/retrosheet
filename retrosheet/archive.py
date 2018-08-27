
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




class Event(object):

    """Events
    Parameters:
        - event_string (NP = No Play)
        - play = {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0, 'run': 0}

    TODO:
        - clean code, make it less redundant, potentially in a module only.
    """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.str = 'NP'
        self.play = {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0, 'run': 0}

    def _print_diamond(self):
        """
        This function prints the diamond for the specific event for easier visualization
        e.g:
        Play: <string>
        |----------[ 2B ]----------|
        |--------------------------|
        |----[ 3B ]-----[ 1B ]-----|
        |--------------------------|
        |------[ H ]---[ B ]-------|
        |--------------------------|
        Runs: [%]    Outs: [%]

        TODO:
            - Log instead of print
        """
        diamond = '''Play: {0}\n|---------[ {3} ]-----------|\n|-------------------------|\n|----[ {4} ]------[ {2} ]-----|\n|-------------------------|\n|------[ {5} ]--[ {1} ]-------|\n|-------------------------|\nRuns: {7}\tOuts: {6}\n'''
        print (diamond.format(self.str, self.play['B'], self.play['1'], self.play['2'],
            self.play['3'], self.play['H'], self.play['out'], self.play['run']))


    def parse_advance(self):
        """
        This portion parses the explicit advancements
        """
        self.play = {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0, 'run': 0} if self.play['out'] >= 3 else self.play
        #####################################
        #this_play = {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0, 'run': 0}
        self.play['B'] = 1

        self.advances = self.str.split('.')[len(self.str.split('.'))-1] if len(self.str.split('.'))>1 else ''

        if re.search('\.', self.str): #there was an advance:
            #test using regular expressions
            #Step2: Understanding advances / outs in advances
            out_in_advance = re.findall('[1-3B]X[1-3H](?:\([^\)]+\))*', self.advances)

            #two type of PLAYER ERRORS on advances:
            #a) notation is out ($X$) but error negates the out. 'X' becomes '-'
            error_out = re.findall('[1-3B]X[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances) #error a

            #b) notation is advance ($-$) and parenthesis explain the error that generated the advance
            ## no action needed. Error is an explanation of play, like all others

            advanced = re.findall('[1-3B]\-[1-3H](?:\([^\)]+\))*', self.advances)

            #element 0 is where they come from
            #element 2 is where they are/were headed
            for oia in out_in_advance:
                self.play[oia[0]] = 0
                self.play['out'] += 1

            for error in error_out:
                if not re.findall('(?:\([1-9U/TH]+\))+', error) or re.findall('^[1-3B]X[1-3H](?:\(TH\))', error): # 'BX3(36)(E5/TH)' and 'BXH(TH)(E2/TH)(8E2)(NR)(UR)' are not errors.
                    self.play['out'] -= 1
                    if error[2] == 'H':
                        self.play[error[0]] = 0 #decrease from where they left
                        self.play[error[2]] += 1 #increase where they touched
                        self.play['run'] += 1
                    else:
                        self.play[error[0]] = 0 #decrease from where they left
                        self.play[error[2]] = 1 #incresae where they touched


            for advance in advanced:
                if advance[2] == 'H':
                    self.play[advance[0]] = 0 #decrease from where they left
                    self.play[advance[2]] += 1 #increase where they touched
                    self.play['run'] += 1
                else:
                    self.play[advance[0]] = 0 #decrease from where they left
                    self.play[advance[2]] = 1 #incresae where they touched

            return True
        return False


    def _left_base(self, arriving_base):
        if arriving_base == 'H':
            self.play['3'] = 0
        elif arriving_base == '1':
            self.play['B'] = 0
        else:
            self.play[str(int(arriving_base)-1)] = 0

        return True


    def _advance(self, arriving_base):
        if arriving_base == 'H':
            self.play[arriving_base] += 1
        else:
            self.play[arriving_base] = 1
        self._left_base(arriving_base)
        return True


    def _out_in_advance(self, arriving_base):
        self.play['out'] += 1
        self._left_base(arriving_base)
        return True


    def _secondary_event(self, secondary_event):
        """
        Events happening with K or Walks. This can be merged with parse_event() if written well
        """
        if re.findall('^CS[23H](?:\([1-9]+\))+',secondary_event):
            #print ('CAUGHT STEALING')
            for cs in secondary_event.split(';'):
                self._out_in_advance(cs[2])

        ##caught stealing errors --> calls reversed:
        elif re.findall('^CS[23H](?:\([1-9]*E[1-9]+)+',secondary_event): # removed last ')' as some observations didnt have it
            for cs in secondary_event.split(';'):
                self._advance(cs[2])

        elif re.findall('^[EOPF][1-3ABI]$',secondary_event):
            pass #explicit event

        elif re.findall('^WP$',secondary_event):
            pass #explicit event (?)

        elif re.findall('^PO[123](?:\([1-9]+\))',secondary_event):
            self.play[secondary_event[2]] = 0
            self.play['out'] += 1

        #only the errors (allowing to stay)
        elif re.findall('^PO[123](?:\([1-9]*E[1-9]+)',secondary_event):
            pass #will keep explicit for now, but it usually shows one base advance.


        #POCS%($$) picked off off base % (2, 3 or H) with the runner charged with a caught stealing
        #without errors
        elif re.findall('^POCS[23H](?:\([1-9]+\))',secondary_event):
            for split in secondary_event.split(';'): #there are CS events together with POCS
                if split[0:2] == 'CS':
                    self.play[split[3]] = 0
                    self.play['out'] += 1
                else: #POCS
                    self.play[split[4]] = 0
                    self.play['out'] += 1

        #only the errors (allowing advances)
        elif re.findall('^POCS[23H](?:\([1-9]*E[1-9]+)', secondary_event):
            pass #will wait for explicit advances


        elif re.findall('^SB[23H]',secondary_event):
            for sb in secondary_event.split(';'):
                if sb[0:2] == 'SB':
                    self._advance(sb[2])

        elif re.findall('^[1-9]*E[1-9]*$',secondary_event): #errors
            pass #wait for explicit change or B-1

        return True


    def parse_event(self):

        if self.str is None:
            pass#return False

        result = ''

        a = self.str.split('.')[0].split('/')[0].replace('!','').replace('#','').replace('?','')
        modifiers = self.str.split('.')[0].split('/')[1:] if len(self.str.split('.')[0].split('/'))>1 else []

        #play['B'] = 1

        #at least one out:
        if re.findall('^[1-9](?:[1-9]*(?:\([B123]\))?)*\+?\-?$',a):
            result = 'out'
            if re.findall('(?:\([B123]\))',a): #double or triple play
                outs = len(re.findall('(?:\([B123]\))',a))
                #check if there is a double play or tripple play
                ################ MODIFIER #####################
                if modifiers:
                    for modifier in modifiers:
                        if re.findall('^[B]?[PUGFL]?DP',modifier): #double play
                            outs = 2
                        elif re.findall('^[B]?[PUGFL]?TP',modifier): #tripple play
                            outs = 3
                ###############################################
                if re.search('(?:\([B]\))',a): #at-bat explicit out
                    for out in re.findall('(?:\([B123]\))',a):
                        if out[1] != 'B':
                            self._out_in_advance(str(int(out[1])+1))
                        else:
                            self._out_in_advance('1')

                elif len(re.findall('(?:\([B123]\))',a)) != outs: #B is implicit
                    # new addition - ad hoc
                    if len(re.findall('(?:\([B123]\))',a)) == 1 and outs == 3 and not re.findall('[B]X[1-3H](?:\([^\)]+\))*', self.advances) :
                        self.play['out'] += 1
                    ###

                    if not re.findall('[1-3B]X[1-3H](?:\([^\)]+\))*', self.advances): #out is implicit in advances too
                        self._out_in_advance('1')

                    elif len(re.findall('[1-3B]X[1-3H](?:\([^\)]+\))*', self.advances)) == len(re.findall('[1-3B]X[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances)):
                        self._out_in_advance('1')

                    for out in re.findall('(?:\([B123]\))',a):
                        self._out_in_advance(str(int(out[1])+1))

                elif not re.search('(?:\([B]\))',a) and len(re.findall('(?:\([B123]\))',a)) == outs:
                    for out in re.findall('(?:\([B123]\))',a):
                        self._out_in_advance(str(int(out[1])+1))
                    self._advance('1')

            else:
                self._out_in_advance('1')

        #out + error: #out is negated
        elif re.findall('^[1-9][1-9]*E[1-9]*$',a):
            result = 'out error'
            if not re.findall('[B]\-[1-3H](?:\([^\)]+\))*', self.advances) or not re.findall('[B]X[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances):
                self.play['B'] = 0
                self.play['1'] = 1

            #wait for explicit change or B-1


        ##caught stealing (except errors):
        elif re.findall('^CS[23H](?:\([1-9]+\))+', a):
            result = 'cs'
            for cs in a.split(';'):
                self._out_in_advance(cs[2])


        ##caught stealing errors --> calls reversed:
        elif re.findall('^CS[23H](?:\([1-9]*E[1-9]+)+',a): # removed last ')' as some observations didnt have it
            result = 'cs error'
            for cs in a.split(';'):
                self._advance(cs[2])


        ##if its a balk
        elif re.findall('^BK$', a):# balk (batter remains but all other get one base)
            result = 'balk'
            pass #will test for explicit

        ##double
        elif re.findall('^D[0-9]*\??$', a):
            result = 'double'
            if not self.play['B'] == 0:
                self.play['2'] = 1
                self.play['B'] = 0

        ##ground rule double (two bases for everyone as ball went out after being in)
        elif re.findall('^DGR[0-9]*$', a):
            result = 'dgr'
            #will keep other advancements explicit. check.
            if not self.play['B'] == 0:
                self.play['2'] = 1
                self.play['B'] = 0

        ## defensive indifference
        elif re.findall('^DI$', a):
            result = 'di'
            pass #explicit advancements

        ## error allowing batter to get on base (B-1 implicit or not)
        elif re.findall('^E[1-9]\??$', a):
            result = 'single'
            if not self.play['B'] == 0:
                self._advance('1')

        # fielders choice (also implicit B-1)
        elif re.findall('^FC[1-9]?\??$',a):
            result = 'single'
            if not self.play['B'] == 0:
                self._advance('1')

        # error on foul fly play (error given to the play but no advances)
        elif re.findall('^FLE[1-9]+$',a):
            result = 'fle'
            pass

        # home run
        elif re.findall('^H[R]?[1-9]*[D]?$',a):
            result = 'hr'
            #will keep other advancements explicit. check.
            if not self.play['B'] == 0:
                self.play['H'] += 1
                self.play['B'] = 0
                self.play['run'] += 1

        ## hit by pitch
        elif re.findall('^HP$', a):
            result = 'single'
            if not self.play['B'] == 0:
                self.play['1'] = 1
                self.play['B'] = 0

        ## intentional walks can happen + SB%, CS%, PO%, PB, WP and E$.
        ## b-1 is implicit + whatever else happens in the play
        elif re.findall('^I[W]?\+?(?:WP)?(?:OA)?(?:SB[23H])?(?:CS[23H](?:\([1-9]+\)))?(?:PO[1-3](?:\([1-9]+\)))?$',a):
            result = 'single'
            if not self.play['B'] == 0:
                self.play['1'] = 1
                self.play['B'] = 0

            other_event = a.split('+')[1] if len(a.split('+'))>1 else []
            if other_event:
                self._secondary_event(other_event)


        #walks. B-1 implicit + other plays
        elif re.findall('^W(?!P)',a):
            result = 'single'
            if not self.play['B'] == 0:
                self.play['1'] = 1
                self.play['B'] = 0

            other_event = a.split('+')[1] if len(a.split('+'))>1 else []
            if other_event:
                self._secondary_event(other_event)

        #elif re.findall('^K$',a):
        #    result = 'out'
        #    self._out_in_advance('1')
        #    if re.findall('[B]X[1-3H](?:\([1-9]+\))*', self.advances):
        #       explicit strikeout
        #       self.play['out'] -= 1

        ## Strikeouts. Events can happen too: SB%, CS%, OA, PO%, PB, WP and E$
        elif re.findall('^K',a):
            result = 'out'
            self._out_in_advance('1')
            #if its a strikeout w fourceout of an explicit out, remove the out here to avoid double-count
            #if re.findall('[B]X[1-3H](?:\([1-9]+\))*', self.advances):
                #explicit strikeout
            #    self.play['out'] -= 1

            if modifiers:
                if modifiers[0] == 'FO' and re.findall('[1-3B]X[1-3H](?:\([^\)]+\))*', self.advances):
                    self.play['out'] -= 1

                if modifiers[0] == 'NDP' and re.findall('[B]\-[1-3H](?:\([^\)]+\))*', self.advances) and re.findall('[1-3B]X[1-3H](?:\([^\)]+\))*', self.advances): #no double play credited
                    self.play['out'] -= 1

                if modifiers[0] == 'TH' and re.findall('[B]X[1-3H](?:\([^\)]+\))*', self.advances):
                    self.play['out'] -= 1


                if modifiers[0] == 'C' and re.findall('[B]X[1-3H](?:\([^\)]+\))*', self.advances):
                    self.play['out'] -= 1

                if modifiers[0] == 'C' and re.findall('[B]\-[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances):
                    self.play['out'] -= 1

                if modifiers[0] =='DP' and re.findall('[B]X[1-3H](?:\([^\)]+\))*', self.advances) and not re.findall('[B]X[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances):
                    self.play['out'] -= 1

                if modifiers[0] =='AP' and re.findall('[B]X[1-3H](?:\([^\)]+\))*', self.advances) and not re.findall('[B]X[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances):
                    self.play['out'] -= 1
                    #total_out = 2
                    #advances_out = len(re.findall('[1-3B]X[1-3H](?:\([^\)]+\))*', self.advances)) - len(re.findall('[1-3B]X[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances))
                    #for out in range(total_out - advances_out):
                    #    self.play['out'] -= 1


                if re.findall('^K$',a) and modifiers[0] == 'MREV' or modifiers == 'UREV':
                    if re.findall('[B]\-[1-3H]', self.advances): #base runner explicit, so no strikeout
                        self.play['out'] -= 1


            elif re.findall('[B]X[1-3H](?:\([^\)]+\))*', self.advances) and not re.findall('[1-3B]X[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances): #Base explicit out
                self.play['out'] -= 1

            elif re.findall('^K$',a) and (re.findall('[B]\-[1-3H](?:\([^\)]+\))*', self.advances) or re.findall('[B]X[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances)): #strike but base runner advanced
                self.play['out'] -= 1

            other_event = a.split('+')[1] if len(a.split('+'))>1 else []
            if other_event:
                # if its a wild pitch and base runner moves explicitly, decrease the out as its no longer a strike:
                if re.findall('[B]\-[1-3H](?:\([^\)]+\))*', self.advances): #Base advanced
                    self.play['out'] -= 1
                    base_advanced = re.findall('[B]\-[1-3H](?:\([^\)]+\))*', self.advances)[0][2]
                    self.play[base_advanced] = 1

                elif re.findall('[B]X[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances):
                    self.play['out'] -= 1
                    base_advanced = re.findall('[B]X[1-3H](?:\([^\)]+\))*(?:\([^\)]*E[^\)]+\))(?:\([^\)]+\))?', self.advances)[0][2]
                    self.play[base_advanced] = 1
                #elif re.findall('[B]X[1-3H](?:\([^\)]+\))*', self.advances): #Base advanced
                #    self.play['out'] -= 1


                self._secondary_event(other_event)

        #No Play == substitution
        elif re.findall('^NP$',a):
            result = 'np'
            pass

        #Unkown Play
        elif re.findall('^(?:OA)?(?:99)?$',a):
            result = 'unkown'
            pass

        ## passed ball - B-1 implicit
        elif re.findall('^PB$', a):
            result = 'single'
            """keeping advancements explicit
            if not play['B'] == 0:
                play['1'] = 1
                play['B'] = 0
            """
        ## PO%($$) picked off of base %(players sequence) (pickoff). Errors negate the out, and runner advance
        #without errors:
        elif re.findall('^PO[123](?:\([1-9]+\))',a):
            result = 'out'
            self.play[a[2]] = 0
            self.play['out'] += 1

        #only the errors (allowing to stay)
        elif re.findall('^PO[123](?:\([1-9]*E[1-9]+)',a):
            result = 'out error'
            pass #will keep explicit for now, but it usually shows one base advance.


        #POCS%($$) picked off off base % (2, 3 or H) with the runner charged with a caught stealing
        #without errors
        elif re.findall('^POCS[23H](?:\([1-9]+\))',a):
            result = 'out'
            for split in a.split(';'): #there are CS events together with POCS
                if split[0:2] == 'CS':
                    self.play[split[3]] = 0
                    self.play['out'] += 1
                else: #POCS
                    self.play[split[4]] = 0
                    self.play['out'] += 1

        #only the errors (allowing advances)
        elif re.findall('^POCS[23H](?:\([1-9]*E[1-9]+)',a):
            pass #will wait for explicit advances

        #single
        elif re.findall('^S[0-9]*\??\+?$',a):
            result = 'single'
            #print ('single')
            if not self.play['B'] == 0:
                self.play['1'] = 1
                self.play['B'] = 0

        #stolen base
        elif re.findall('^SB[23H]',a):
            result = 'sb'
            for sb in a.split(';'):
                if sb[0:2] == 'SB':
                    self._advance(sb[2])

        #tripple
        elif re.findall('^T[0-9]*\??\+?$',a):
            result = 'tripple'
            if not self.play['B'] == 0:
            #other advances explicit
                self.play['3'] = 1
                self.play['B'] = 0

        ## wild pitch - base runner advances
        elif re.findall('^WP', a):
            result = 'single'
            if not self.play['B'] == 0:
                self.play['1'] = 1
                self.play['B'] = 0

        elif re.findall('^C$', a):
            #What is "C" - strikeout ??
            pass
            #result = 'single'
            #self.play['out'] += 1
            #self.play['B'] = 0

        else:
            raise EventNotFoundError('Event Not Known', a)

        #self._print_diamond()
        #print (result)
        return True


    def decipher(self):
        self.parse_advance()
        self.parse_event()
