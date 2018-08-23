# encoding: utf-8

import logging
import re
from .helpers import out_in_advance, advance_base


class Event1(object):
    """
    New Parsing class
    """


    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.str = 'NP'
        self.play = {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0, 'run': 0}
        self.batting_lineup = {'1':'', '2':'','3':'', '4':'','5':'','6':'','7':'','8':'','9':''}
        self.fielding_lineup = {'1':'', '2':'','3':'', '4':'','5':'','6':'','7':'','8':'','9':''}


    def _initialize_modifiers(self):
        self.modifiers = {
        'out': 0, 'run': 0, 'bunt': 0, 'trajectory': '','location': '',
        'errors':[], 'interference':'', 'review': '','foul': 0, 'force out': 0,
        'throw':0, 'sacrifice': '', 'relay':0, 'other':[], 'courtesy':'','passes': ''
        }


    def _modifiers(self):
        """
        """
        ### Play Modifier:
        for mpm in self.mpm:
            mpm = mpm.replace('#','').replace('-','').replace('+','')\
                    .replace('!','').replace('?','').upper()

            if re.findall('^[B]?[PUGFL]?DP$',mpm): #double play
                self.modifiers['out'] = 2
                self.modifiers['bunt'] = 1 if mpm[0]=='B' else 0
                if self.modifiers['trajectory'] == '':
                    self.modifiers['trajectory'] = mpm[1] if mpm[1] in ['PGFL'] else ''
                    self.modifiers['trajectory'] = mpm[0] if mpm[0] in ['PGFL'] else ''
            elif re.findall('^[B]?[PUGFL]?TP$',mpm): #tripple play
                self.modifiers['out'] = 3
            elif re.findall('^[B]$',mpm): #tripple play
                self.modifiers['bunt'] = 1
            elif re.findall('^COU[BFR]$',mpm): #courtesy batter , fielder, runner
                self.modifiers['courtesy'] = mpm[3]
            elif re.findall('^[BFRU]?INT$', mpm): #interception
                self.modifiers['interference'] = mpm[0] if mpm[0] in ['B','F','R','U'] else ''
            elif re.findall('^[MU]REV$', mpm): #review
                self.modifiers['review'] = mpm[0]
            elif re.findall('^FL$', mpm): #foul
                self.modifiers['foul'] = 1
            elif re.findall('^FO$', mpm): #force out
                self.modifiers['force out']= 1
            elif re.findall('^TH[H]?[1-9\)]*$', mpm): #throw
                self.modifiers['throw']= 1
            elif re.findall('^S[FH]$', mpm): #sacrifice hit or fly
                self.modifiers['sacrifice']= mpm[1]
                self.modifiers['bunt'] = 1 if mpm[1]=='H' else 0 #sacrifice hit is a bunt
            elif re.findall('^[U]?[6]?R[0-9URNHBS]*(?:\(TH\))?$', mpm): #relay
                self.modifiers['relay'] = 1
                self.modifiers['passes'] = mpm
                if re.findall('TH',mpm):
                    self.modifiers['throw'] = 1
            elif re.findall('^E[1-9]*$', mpm): #error on $
                self.modifiers['errors'].append(mpm[1]) if len(mpm)>1 else ''
            elif mpm in ['AP','BOOT','IPHR','NDP','BR','IF','OBS','PASS','C','U','RNT']: #other #U for unkown
                self.modifiers['other'].append(mpm)
            elif re.findall('^B?[PGFL][1-9MLRDXSF]?[1-9LRMXDSFW]*$',mpm):
                self.modifiers['bunt'] = 1 if mpm[0] =='B' else 0
                if self.modifiers['trajectory'] =='':
                    self.modifiers['trajectory'] = mpm[1] if mpm[0] =='B' else mpm[0]
                if self.modifiers['location'] == '':
                    self.modifiers['location'] = mpm[2:] if mpm[0] =='B' else mpm[1:]
            elif re.findall('^[BU]?[1-9MLRDXSF][1-9LRMXDSFW]*$' ,mpm):
                self.modifiers['bunt'] = 1 if mpm[0] =='B' else 0
                self.modifiers['location'] = mpm
            elif mpm == '' or mpm=='U4U1':
                pass
            else:
                self.log.debug('Event Not Known: {0}'.format(mpm))


    def _describers(self):
        ### Play describers:
        pass


    def _advances(self):
        ### Explicit advances
        self.advances={'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0,'run': 0}

        for loop, move in enumerate(self.em):
            move = move[0]
            if re.findall('X', move):
                self.advances = out_in_advance(self.advances, bfrom=move[0], bto=move[2])
            elif re.findall('\-', move):
                self.advances = advance_base(self.advances, bfrom=move[0], bto=move[2])
            else:
                self.log.debug('Explicit move not found: {0}'.format(move))


    def _main_play(self):
        self.main_play={'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0,'run': 0, 'outcome':[]}

        mp = self.mp[0].replace('#','').replace('!','').replace('?','')
        #mp = 'NP' if not mp or mp == '' else mp

        if re.findall('^[1-9](?:[1-9]*(?:\([B123]\))?)*\+?\-?$', mp): # implicit B out
            self.main_play =  out_in_advance(self.main_play)#at bat is out
            for base_out in re.findall('(?:\([123]\))', mp): self.main_play = out_in_advance(self.main_play, bfrom=base_out[1]) #excluding at bat
        elif re.findall('^[1-9][1-9]*E[1-9]*$', mp): #error on out, B-1 implicit if not explicit
            self.main_play = advance_base(self.main_play) #B-1 except if explicily moving on advances
        elif re.findall('^CS[23H](?:\([1-9]+\))+', mp):##caught stealing (except errors):
            for cs in mp.split(';'): self.main_play = out_in_advance(self.main_play, bto=cs[2])
        elif re.findall('^CS[23H](?:\([1-9]*E[1-9]+)+', mp): ## caught stealing errors
            for cs in mp.split(';'): self.main_play = advance_base(self.main_play, bto=cs[2])
        elif re.findall('^BK$', mp):# balk (batter remains but all other get one base)
            pass
        elif re.findall('^D[0-9]*\??$', mp): #double
            self.main_play = advance_base(self.main_play, bto='2',bfrom='B')
        elif re.findall('^DGR[0-9]*$', mp): #ground rule double (two bases for everyone as ball went out after being in)
            self.main_play = advance_base(self.main_play, bto='2',bfrom='B')
        elif re.findall('^DI$', mp): #defensive indifference
            pass
        elif re.findall('^E[1-9]\??$', mp): ## error allowing batter to get on base (B-1 implicit or not)
            self.main_play = advance_base(self.main_play)
        elif re.findall('^FC[1-9]?\??$',mp):# fielders choice (also implicit B-1)
            self.main_play = advance_base(self.main_play)
        elif re.findall('^FLE[1-9]+$',mp): # error on foul fly play (error given to the play but no advances)
            pass
        elif re.findall('^H[R]?[1-9]*[D]?$', mp): #home run
            self.main_play = advance_base(self.main_play, bto='H',bfrom='B')
        elif re.findall('^HP$', mp): #hit by pitch
            self.main_play = advance_base(self.main_play)
        elif re.findall('^W',mp): # walk
            self.main_play = advance_base(self.main_play)
        elif re.findall('^I[W]?',mp): # intentional walk
            self.main_play = advance_base(self.main_play)
        elif re.findall('^K',mp): #strikeout
            self.main_play = out_in_advance(self.main_play)
        elif re.findall('^NP$',mp): #no play
            pass
        elif re.findall('^(?:OA)?(?:99)?$',mp): #unkown play
            pass
        elif re.findall('^PB$', mp): #passed ball
            self.main_play = advance_base(self.main_play)
        elif re.findall('^PO[123](?:\([1-9]+\))',mp): #picked off of base (without error)
            self.main_play = out_in_advance(self.main_play, bfrom=mp[2])
        elif re.findall('^PO[123](?:\([1-9]*E[1-9]+)',mp): #pick off with pass error (no out nothing implicit)
            pass
        elif re.findall('^POCS[23H](?:\([1-9]+\))',mp): #POCS%($$) picked off off base % (2, 3 or H) with the runner charged with a caught stealing
            for split in mp.split(';'): self.main_play = out_in_advance(self.main_play, bto=split[2]) if split[0:2] == 'CS' else  out_in_advance( self.main_play, bto=split[4])  #there are CS events together with POCS
        elif re.findall('^POCS[23H](?:\([1-9]*E[1-9]+)',mp):#POCS errors
            pass
        elif re.findall('^S[0-9]*\??\+?$',mp): #single
            self.main_play = advance_base(self.main_play)
        elif re.findall('^SB[23H]',mp): #stolen base
            for sb in mp.split(';'): self.main_play = advance_base(self.main_play, bto=sb[2]) if sb[0:2] == 'SB' else self.main_play
        elif re.findall('^T[0-9]*\??\+?$',mp): #triple
            self.main_play = advance_base(self.main_play, bfrom='B', bto='3')
        elif re.findall('^WP', mp): ## wild pitch - base runner advances
            self.main_play = advance_base(self.main_play)
        elif re.findall('^C$', mp): #usualy 3rd strikeout but not always clear
            pass
        else:
            self.log.debug('Main event not known: {0}'.format(mp))
            #raise EventNotFoundError('Event Not Known', mp)


    def _split_plays(self):
        """
        split the play into:
            - main play --> main string
            - implicit advances --> calculated
            - main play modifiers --> separated by '/'
            - secondary_play --> (for K+ and [I]W+ events)

            - explicit advances --> separated from main play by '.'. It is = explicit move + advance description + advance modifiers
            - explicit move --> the move of players, without modifiers. base-base or baseXbase
            - advance description --> descriptors only, enclosed by '()'
            - advance modifiers --> modifiers for the description, separated by '/'
        """
        self.mp = []  # main play
        self.mpm= []  # main play modifiers, preceeded by '/'
        self.mpd = [] # main play describers, inside '()'

        self.mpdm = []# main play describer modifiers, preceeded by '/' #not in use for now

        self.sp = []  # secondary play
        self.spm = [] # secondary play modifiers, preceeded by '/'

        self.ea = []  # explicit advances
        self.em = []  # explicit move
        self.ad = []  # advance descriptions
        self.am = []  # advance modifiers

        #main part:
        self.mp = re.findall('^(?:[^\.^\+^/]+)', self.str.split('.')[0].split('+')[0])#self.str.split('.')[0]
        #print ('\nmp:\t', self.mp)

        self.mpm = re.findall('(?<=/)[^\+^/]+', self.str.split('.')[0].split('+')[0])
        #print ('\nmpm:\t', self.mpm)

        self.mpd = re.findall('(?<=\()(?:[^\)^/])+', self.str.split('.')[0].split('+')[0])
        #print ('\nmpd\t', self.mpd)


        #secondary play

        self.sp = re.findall('(?<=\+)(?:[^\.^\+^/]+)', self.str.split('.')[0])
        #print ('\nsp:\t', self.sp)

        str_spm = self.str.split('.')[0].split('+',1)[1] if len(self.str.split('.')[0].split('+',1)) > 1 else ''
        self.spm = re.findall('(?<=/)(?:[^/^\+]+)', str_spm)
        #print ('\nspm:\t', self.spm)

        #advances:
        self.ea = self.str.split('.')[len(self.str.split('.'))-1].split(';') if len(self.str.split('.'))>1 else []
        for advance in self.ea: self.em.append(re.findall('[1-3B][\-X][1-3H]', advance))
        for advance in self.ea: self.ad.append(re.findall('(?<=\()(?:[^\)^/]+)', advance))
        for advance in self.ea:
            describers = re.findall('(?<=\()(?:[^\)]+)', advance)
            if not describers:
                self.am.append([[]])
            else:
                temp = []
                for describer in describers:
                    temp.append(re.findall('(?<=/)[^/^\)]+', describer))
                self.am.append(temp)

        #print ('\nea:\t', self.ea)
        #print ('\nem:\t', self.em)
        #print ('\nad:\t', self.ad)
        #print ('\nam:\t', self.am)


    def parse_event(self):
        """
        """
        self._split_plays()

        self._initialize_modifiers()
        self._modifiers()
        self._main_play()
        self._advances()


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


class EventNotFoundError(Exception):
    """ Exception that is raised when an event is not recognized
    """
    def __init__(self, error, event):
        self.log = logging.getLogger(__name__)
        self.log.debug("Event not found: {0}".format(event))
        super(EventNotFoundError, self).__init__(event)
