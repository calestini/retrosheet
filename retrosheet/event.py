# encoding: utf-8

import logging
import re

class Event(object):

    """Events
    Parameters:
        - event_string
        - play = {'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0, 'run': 0}

    Clean code, make it less redundant, potentially in a module only.
    """

    def __init__(self, event_string='NP', play={'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0, 'run': 0}):
        self.log = logging.getLogger(__name__)
        self.str = event_string
        self.play = play

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

        ##double plays
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
        #add code here to mark all bases stolen (1,2 or 3 in the same play)

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
        #self.log = logging.getLogger(__name__)
        #self.log.debug("Event not found")
        super(EventNotFoundError, self).__init__(event)
