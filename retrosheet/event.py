# encoding: utf-8

import logging
import re
from .helpers import (
out_in_advance, advance_base,
PREVIOUS_BASE, NEXT_BASE, pitch_count,
move_base, leave_base
)


class event(object):
    """
    New event parsing class. This will worry only with the current event string.
    Any contextual information will be taken by the Game class (player_id, pitcher, etc).
    The objective is to map everything that happened, by all players, for quick
    reference.

    TODO:remove redundancies
    """

    def __init__(self):

        self.log = logging.getLogger(__name__)
        self.str = 'NP'
        self.base = {'B': None,'1': None,'2': None,'3': None, 'H':[]}
        self.advances={'B': 1,'1': 0,'2': 0,'3': 0,'H': 0, 'out': 0,'run': 0}


    #def _initialize_modifiers(self):
    def _is_explicit(self, bfrom='B'):
        for em in self.em:
            if em[0][0]==bfrom:
                #self.log.debug('{0} is explicit'.format(bfrom))
                return True
        #self.log.debug('{0} is not explicit'.format(bfrom))
        return False

    def _modifiers(self, modifiers):
        """
        """
        ### Play Modifier:
        for mpm in modifiers:
            mpm = mpm.replace('#','').replace('-','').replace('+','')\
                    .replace('!','').replace('?','').upper()

            if re.findall('^[B]?[PUGFL]?DP$',mpm): #double play
                #self.main_play['out'] = 2
                self.modifiers['DP'] = True
                self.modifiers['bunt'] = 1 if mpm[0]=='B' else 0
                if self.modifiers['trajectory'] == '':
                    self.modifiers['trajectory'] = mpm[1] if mpm[1] in ['PGFL'] else ''
                    self.modifiers['trajectory'] = mpm[0] if mpm[0] in ['PGFL'] else ''
            elif re.findall('^[B]?[PUGFL]?TP$',mpm): #tripple play
                #self.main_play['out'] = 3
                self.modifiers['TP'] = True
            elif re.findall('^U[1-9]+', mpm):
                self.modifiers['passes'].append(mpm)
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
                self.modifiers['passes'].append(mpm)
                if re.findall('TH',mpm):
                    self.modifiers['throw'] = 1
            elif re.findall('^E[1-9]*$', mpm): #error on $
                error = re.findall('^E[1-9]*$', mpm)
                if 'TH' in mpm:
                    self.stats['fielding'].append(['E(TH)', error[0][1]])
                else:
                    self.stats['fielding'].append(['E', error[0][1]])

                #self.modifiers['errors'].append(mpm[1]) if len(mpm)>1 else ''
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


    def _advances(self):
        ### Explicit advances
        self.ad_out = 0

        for loop, move in enumerate(self.em):
            error = None
            error_loop = None
            #each element is a list
            move = move[0] #--> retrieve string
            bfrom = move[0]
            bto = move[2]
            if re.findall('X', move):
                #it could be on error or not
                was_out = None
                #if describer is numbers only, it was not an error.
                if self.ad[loop]: #there is a modifier

                    for desc_loop, desc in enumerate(self.ad[loop]):
                        if re.findall('^[1-9U]+$', desc):
                            was_out = True
                            was_out_loop =desc_loop

                    if was_out:#re.findall('^[1-9U]+$', self.ad[loop][0]):
                        #print ('was out')
                        #print (bfrom, bto)
                        self.advances = out_in_advance(self.advances, bfrom=bfrom, bto=bto)
                        self.ad_out +=1

                        self.base = leave_base(self.base, bfrom=bfrom)

                        ###########################   stats   ##############################
                        PO = re.findall('[1-9U]$',self.ad[loop][was_out_loop])
                        if PO:
                            self.stats['fielding'].append(['PO',PO[-1]])

                        As = re.findall('[1-9U]+', self.ad[loop][was_out_loop])
                        if As:
                            As = As[0]
                            for a in As:
                                self.stats['fielding'].append(['A',a]) if a not in PO else None

                        self.stats['running'].append(['PO',bfrom, bto])
                        ###########################   end   ##############################
                        passes = re.findall('[1-9U]+',self.ad[loop][was_out_loop])
                        #append pass sequence (for location purposes)
                        self.modifiers['passes'].append(passes[0]) if passes else None

                    else:
                        for describer_loop, describer in enumerate(self.ad[loop]):
                            if re.findall('[1-9]*E[1-9]',describer):
                                error = re.findall('E[1-9]',describer)[0]
                                error_loop = describer_loop

                        if error:
                            self.move_on_error.append(bto)
                            self.advances = advance_base(self.advances, bfrom=bfrom, bto=bto)
                            self.base = move_base( self.base, bfrom=bfrom, bto=bto)

                            ###########################   stats   ##############################
                            #error describer
                            error_modifier = self.am[loop][error_loop][0] if self.am[loop][error_loop] else ''
                            if re.sub('[1-9U]','', error_modifier) == 'TH':
                                self.stats['fielding'].append(['E(TH)', error[-1]])
                            else:
                                self.stats['fielding'].append(['E', error[-1]])

                            #append pass sequence (for location purposes)
                            passes = re.sub('[^0-9]','', error+error_modifier)
                            self.modifiers['passes'].append(passes) if passes else None

                            if move[2] == 'H':
                                run_describer = 'R'
                                run_describer += '(UR)' if 'UR' in self.ad[loop] else ''
                                run_describer += '(NR)' if 'NR' in self.ad[loop] else ''
                                run_describer += '(RBI)' if 'RBI' in self.ad[loop] else ''
                                run_describer += '(NORBI)' if 'NORBI' in self.ad[loop] else ''
                                run_describer += '(TUR)' if 'TUR' in self.ad[loop] else ''

                                self.stats['running'].append([run_describer,bfrom, bto])

                            ###########################   end   ##############################

                        else:
                            self.advances = out_in_advance(self.advances, bfrom=bfrom, bto=bto)
                            self.base = leave_base(self.base, bfrom=bfrom)
                            self.ad_out +=1
                            ###########################   stats   ##############################
                            PO = re.findall('[1-9U]$',self.ad[loop][0]) if self.ad[loop] else None
                            if PO:
                                self.stats['fielding'].append(['PO',PO[0]])

                            As = re.findall('[1-9U]+', self.ad[loop][0]) if self.ad[loop] else None
                            if As:
                                As = As[0]
                                for a in As:
                                    self.stats['fielding'].append(['A',a]) if a not in PO else None

                            self.stats['running'].append(['PO',bfrom, bto])
                            ###########################   end   ##############################
                            passes = re.findall('[1-9U]+',self.ad[loop][0]) if self.ad[loop] else None
                            #append pass sequence (for location purposes)
                            self.modifiers['passes'].append(passes[0]) if passes else None

                            #map other errors, if existing (remove error modifier loop)

                        if len(self.ad[loop]) > 1:
                            for loop2, describer in enumerate(self.ad[loop][1:]):
                                if loop2 != error_loop:
                                    other_error = re.findall('E[1-9]',describer)
                                    if other_error:

                                        error_modifier = self.am[loop][loop2][0] if self.am[loop][loop2] else ''
                                        #print ('error modifier', error_modifier)
                                        if re.sub('[1-9U]','', error_modifier) == 'TH':
                                            self.stats['fielding'].append(['E(TH)', other_error[0][-1]])
                                        else:
                                            self.stats['fielding'].append(['E', other_error[0][-1]])

                                        #append pass sequence (for location purposes)
                                        passes = re.sub('[^0-9]','', other_error[0]+error_modifier)
                                        self.modifiers['passes'].append(passes) if passes else None
                '''
                for describer_loop, describer in enumerate(self.ad[loop]):
                    if re.findall('E[1-9]',describer):
                        error = re.findall('E[1-9]',describer)[0]
                        error_loop = describer_loop

                if error:
                    self.advances = advance_base(self.advances, bfrom=bfrom, bto=bto)

                    ###########################   stats   ##############################
                    #error describer
                    error_modifier = self.am[loop][error_loop][0] if self.am[loop][error_loop] else ''
                    if re.sub('[1-9U]','', error_modifier) == 'TH':
                        self.stats['fielding'].append(['E(TH)', error[1]])
                    else:
                        self.stats['fielding'].append(['E', error[1]])

                    #append pass sequence (for location purposes)
                    passes = re.sub('[^0-9]','', error+error_modifier)
                    self.modifiers['passes'].append(passes) if passes else None

                    if move[2] == 'H':
                        run_describer = 'R'
                        run_describer += '(UR)' if 'UR' in self.ad[loop] else ''
                        run_describer += '(NR)' if 'NR' in self.ad[loop] else ''
                        run_describer += '(RBI)' if 'RBI' in self.ad[loop] else ''
                        run_describer += '(NORBI)' if 'NORBI' in self.ad[loop] else ''
                        run_describer += '(TUR)' if 'TUR' in self.ad[loop] else ''

                        self.stats['running'].append([run_describer,bfrom, bto])

                    ###########################   end   ##############################


                else:
                    self.advances = out_in_advance(self.advances, bfrom=bfrom, bto=bto)

                    ###########################   stats   ##############################
                    PO = re.findall('[1-9U]$',self.ad[loop][0]) if self.ad[loop] else None
                    if PO:
                        self.stats['fielding'].append(['PO',PO[0]])

                    As = re.findall('[1-9U]+', self.ad[loop][0]) if self.ad[loop] else None
                    if As:
                        As = As[0]
                        for a in As:
                            self.stats['fielding'].append(['A',a]) if a not in PO else None

                    self.stats['running'].append(['PO',bfrom, bto])
                    ###########################   end   ##############################
                    passes = re.findall('[1-9U]+',self.ad[loop][0]) if self.ad[loop] else None
                    #append pass sequence (for location purposes)
                    self.modifiers['passes'].append(passes[0]) if passes else None

                    #map other errors, if existing (remove error modifier loop)
                    if len(self.ad[loop]) > 1:
                        for loop2, describer in enumerate(self.ad[loop][1:]):
                            other_error = re.findall('[1-9]*E[1-9]',describer)
                            if other_error:

                                error_modifier = self.am[loop][loop2][0] if self.am[loop][loop2] else ''
                                #print ('error modifier', error_modifier)
                                if re.sub('[1-9U]','', error_modifier) == 'TH':
                                    self.stats['fielding'].append(['E(TH)', other_error[0][-1]])
                                else:
                                    self.stats['fielding'].append(['E', other_error[0][-1]])

                                #append pass sequence (for location purposes)
                                passes = re.sub('[^0-9]','', other_error[0]+error_modifier)
                                self.modifiers['passes'].append(passes) if passes else None

                    '''
            elif re.findall('\-', move):
                bfrom = move[0]
                bto = move[2]
                self.advances = advance_base(self.advances, bfrom=bfrom, bto=bto)
                self.base = move_base(self.base, bfrom=bfrom, bto=bto)
                ###########################   stats   ##############################
                if bto == 'H':
                    run_describer = 'R'
                    run_describer += '(UR)' if 'UR' in self.ad[loop] else ''
                    run_describer += '(NR)' if 'NR' in self.ad[loop] else ''
                    run_describer += '(RBI)' if 'RBI' in self.ad[loop] else ''
                    run_describer += '(NORBI)' if 'NORBI' in self.ad[loop] else ''
                    run_describer += '(TUR)' if 'TUR' in self.ad[loop] else ''

                    self.stats['running'].append([run_describer,bfrom, bto])

                for describer_loop, describer in enumerate(self.ad[loop]):
                    if re.findall('[1-9]*E[1-9]',describer):
                        error = re.findall('E[1-9]',describer)[0]
                        error_loop = describer_loop
                        #print ('loop', loop,'error', error,'error loop', error_loop)

                if error:
                    error_modifier = self.am[loop][error_loop][0] if self.am[loop][error_loop] else ''
                    #print (self.am, self.str)

                    if re.sub('[1-9U]','', error_modifier) == 'TH':
                        self.stats['fielding'].append(['E(TH)', error[-1]])
                    else:
                        self.stats['fielding'].append(['E', error[-1]])

                    #append pass sequence (for location purposes)
                    passes = re.sub('[^0-9]','', error[0]+error_modifier)
                    self.modifiers['passes'].append(passes) if passes else None

                ###########################   end   ##############################

                #map other errors, if existing (remove error modifier loop)
                if len(self.ad[loop]) > 1:

                    for loop2, describer in enumerate(self.ad[loop]):
                        if loop2 != error_loop:
                            other_error = re.findall('[1-9]*E[1-9]',describer)
                            if other_error:

                                error_modifier = self.am[loop][loop2][0] if self.am[loop][loop2] else ''
                                #print ('error modifier', error_modifier)
                                if re.sub('[1-9U]','', error_modifier) == 'TH':
                                    self.stats['fielding'].append(['E(TH)', other_error[0][-1]])
                                else:
                                    self.stats['fielding'].append(['E', other_error[0][-1]])

                                #append pass sequence (for location purposes)
                                passes = re.sub('[^0-9]','', other_error[0]+error_modifier)
                                self.modifiers['passes'].append(passes) if passes else None

            else:
                self.log.debug('Explicit move not found: {0}'.format(move))

    """"""
    def _play_null(self):
        self.main_play =  out_in_advance(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play#at bat is out
        self.base = leave_base(self.base, bfrom='B') if not self._is_explicit() else self.base

    def _play_flyout(self):
        if 'FO' not in mpm:
            self.main_play =  out_in_advance(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play#at bat is out
            self.base = leave_base(self.base, bfrom='B') if not self._is_explicit() else self.base

        if 'FO' in mpm and not re.findall('B', mp):
            self.main_play = advance_base(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play #B-1 except if explicily moving on advances
            self.base = move_base(self.base, bfrom='B', bto='1')

        PO = mp[-1]
        As = mp[:-1]
        if As:
            for a in As: self.stats['fielding'].append(['A',a])

        self.stats['batting'].append(['SF',''])  if 'SF' in mpm else None
        self.stats['batting'].append(['SH',''])  if 'SH' in mpm else None
        self.stats['batting'].append(['GDP',''])  if 'GDP' in mpm else None

        passes = re.sub('(?:\([^\)]+\))','',mp)
        self.modifiers['passes'].append(passes)

    def _play_pass_outs(self):
        for base_out in re.findall('(?:\([B123]\))', mp):
            self.main_play = out_in_advance(self.main_play, bfrom=base_out[1]) #excluding at bat
            self.base = leave_base(self.base, bfrom=base_out[1])

        if 'FO' in mpm and not re.findall('B', mp):
            self.main_play = advance_base(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play #B-1 except if explicily moving on advances
            self.base = move_base(self.base, bfrom='B', bto='1')


        #Testing for double play
        double_play = False
        triple_play = False

        if 'BGDP' in mpm or 'BPDP' in mpm or 'DP' in mpm or 'FDP'in mpm or 'GDP' in mpm or 'LDP' in mpm:
            double_play = True

        if 'BGTP' in mpm or 'BPTP' in mpm or 'TP' in mpm or 'FTP' in mpm or 'GTP' in mpm or 'LTP' in mpm:
            triple_play = True


        if double_play and self.main_play['out'] + self.ad_out < 2:
            if 'FO' not in mpm:
                self.main_play =  out_in_advance(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play#at bat is out
                self.base = leave_base(self.base, bfrom='B') if not self._is_explicit() else self.base
            else:
                self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base

        if triple_play and self.main_play['out'] + self.ad_out < 3:
            if 'FO' not in mpm:
                self.main_play =  out_in_advance(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play#at bat is out
                self.base = leave_base(self.base, bfrom='B') if not self._is_explicit() else self.base
            else:
                self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base

        ###########################   stats   ##############################
        fielder1 = re.findall('^[1-9]$', mp) #flyball, not always present
        fielders2 = re.findall('[1-9]\(', mp)#$$()$ play, with explicit outs
        fielders2 = [x.replace('(','') for x in fielders2] if fielders2 else []
        fielders3 = re.findall('^[1-9][1-9]+$', mp) #when its a sequence and out
        fielders3 = [fielders3[0][-1]] if fielders3 else []
        fielders4 = [mp[-1]] if re.findall('[1-9]$', mp) and 'GDP' in mpm  else [] #it was a Ground into Double Play

        POs = fielder1 + fielders2 + fielders3 + fielders4

        double_play = False
        triple_play = False

        if 'BGDP' in mpm or 'BPDP' in mpm or 'DP' in mpm or 'FDP'in mpm or 'GDP' in mpm or 'LDP' in mpm:
            double_play = True

        if 'BGTP' in mpm or 'BPTP' in mpm or 'TP' in mpm or 'FTP' in mpm or 'GTP' in mpm or 'LTP' in mpm:
            triple_play = True

        for po in POs:
            self.stats['fielding'].append(['PO',po[0]])
            self.stats['fielding'].append(['DP',po[0]]) if double_play else None
            self.stats['fielding'].append(['TP',po[0]]) if triple_play else None

        all_fielders_touched = re.sub(r'\([^)]*\)', '', mp)
        for fielder in all_fielders_touched:
            if fielder not in POs:
                self.stats['fielding'].append(['A',fielder])


        self.stats['batting'].append(['SF',''])  if 'SF' in mpm else None
        self.stats['batting'].append(['SH',''])  if 'SH' in mpm else None
        self.stats['batting'].append(['GDP',''])  if 'GDP' in mpm else None

        passes = re.sub('(?:\([^\)]+\))','',mp)
        self.modifiers['passes'].append(passes)

    def _play_error_on_out(self):
        self.main_play = advance_base(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play #B-1 except if explicily moving on advances
        self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances

        ###########################   stats   ##############################
        error_fielder = re.findall('E[1-9]$', mp)[0]
        self.stats['fielding'].append(['E',error_fielder[1]])

    def _play_cs(self):
        for cs in mp.split(';'):
            bto = cs[2]
            bfrom = PREVIOUS_BASE[cs[2]]
            self.main_play = out_in_advance(self.main_play, bto=cs[2])
            self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit() else self.base

            ###########################   stats   ##############################
            self.stats['running'].append(['CS',bfrom, bto])

            PO = re.findall('[1-9]\)', cs)
            if PO:
                PO = PO[0].replace(')','')
                self.stats['fielding'].append(['PO',PO[0]])

            As = re.findall('(?:\([^\(]+\))', cs)
            if As:
                As = As[0].replace('(','').replace(')','')
                for a in As:
                    if a not in PO:
                        self.stats['fielding'].append(['A',a])

            passes = re.sub('CS[23H]','', cs).replace('(','').replace(')','').replace('E','')
            if passes:
                self.modifiers['passes'].append(passes)
            ###########################   end   ################################

    def _play_cs_error(self):
        #the advance could also be explicit given the error, for more than one base.
        for cs in mp.split(';'):
            bto = cs[2]
            bfrom = PREVIOUS_BASE[cs[2]]
            self.main_play = advance_base(self.main_play, bto=bto) if not self._is_explicit(bfrom=bfrom) else self.main_play
            self.base = move_base(self.base, bfrom=bfrom, bto=bto) if not self._is_explicit(bfrom=bfrom) else self.base #B-1 except if explicily moving on advances

            ###########################   stats   ##############################
            self.stats['running'].append(['CS(E)',bfrom, bto]) #caught stealing w error

            As = re.findall('^(?:\([1-9]+E)+', cs)
            if As:
                As = As[0].replace('E','').replace('(','')
                for a in As:
                    self.stats['fielding'].append(['A',a])


            error_fielder = re.findall('E[1-9]', cs)[0]
            self.stats['fielding'].append(['E',error_fielder[1]])

            passes = re.sub('CS[23H]','', cs).replace('(','').replace(')','').replace('E','')
            if passes:
                self.modifiers['passes'].append(passes)
            ###########################   end   ################################

    def _play_balk(self):
        self.stats['pitching'].append(['BK','1'])

    def _play_double(self):
        self.main_play = advance_base(self.main_play, bto='2',bfrom='B') if not self._is_explicit() else self.main_play
        self.base = move_base(self.base, bfrom='B', bto='2') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
        ###########################   stats   ##############################
        self.stats['batting'].append(['2B',''])
        self.stats['batting'].append(['H','']) #hit
        self.stats['pitching'].append(['H','1'])

        passes = re.findall('[0-9]', mp)
        if passes:
            self.modifiers['passes'].append(passes[0])
        ###########################   end   ################################

    def _play_grd(self): #ground rule double
        self.main_play = advance_base(self.main_play, bto='2',bfrom='B')  if not self._is_explicit() else self.main_play
        self.base = move_base(self.base, bfrom='B', bto='2') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
        ###########################   stats   ##############################
        self.stats['batting'].append(['DGR',''])
        self.stats['batting'].append(['H','']) #hit
        self.stats['pitching'].append(['H','1'])

        passes = re.findall('[0-9]+', mp)
        if passes:
            self.modifiers['passes'].append(passes[0])

    def _play_di(self): #defensive indiference
        ###########################   stats   ##############################
        for explicit_move in self.em:
            bto = explicit_move[0][2]
            bfrom = explicit_move[0][0]
            self.stats['running'].append(['DI',bfrom, bto])
        ###########################   end   ################################

    def _play_error2(self):
        self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
        self.base = move_base(self.base, bfrom='B',bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
        ###########################   stats   ##############################
        error_fielder = re.findall('E[1-9]$', mp)[0]
        if 'TH' in mpm: #throwing error
            self.stats['fielding'].append(['E(TH)',error_fielder[1]])
        else:
            self.stats['fielding'].append(['E',error_fielder[1]])

        passes = re.findall('[0-9]+', mp)
        if passes:
            self.modifiers['passes'].append(passes[0])
        ###########################   end   ################################

    def _play_fc(self): #fielder's choice
        self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
        self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
        ###########################   stats   ##############################
        self.stats['batting'].append(['FC',''])
        if len(mp) > 2:
            self.stats['fielding'].append(['FC',mp[2]])
            self.modifiers['passes'].append(mp[2])
        ###########################   end   ################################

    def _play_fle(self): # error on foul fly play (error given to the play but no advances)
        ###########################   stats   ##############################
        self.stats['fielding'].append(['FLE',mp[3]])
        ###########################   end   ################################

    def _play_home_run(self):
        self.main_play = advance_base(self.main_play, bto='H',bfrom='B')  if not self._is_explicit() else self.main_play
        self.base = move_base(self.base, bfrom='B', bto='H') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
        ###########################   stats   ##############################
        self.stats['running'].append(['R','B', 'H'])

        self.stats['batting'].append(['HR','']) #home run
        self.stats['pitching'].append(['HR','1'])

        self.stats['batting'].append(['H','']) #hit
        self.stats['pitching'].append(['H','1'])

        self.stats['batting'].append(['R','']) #run

        if 'IPHR' in mpm:
            self.stats['batting'].append(['IPHR',''])
        ###########################   end   ################################

    def _play_hb(self):
        self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
        self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
        ###########################   stats   ##############################
        self.stats['batting'].append(['HBP','']) #hit by pitch
        ###########################   end   ################################

    def _play_walk(self):
        self.main_play = advance_base(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play
        self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
        ###########################   stats   ##############################
        self.stats['batting'].append(['BB','']) #base on balls
        self.stats['pitching'].append(['BB','1']) #base on balls
        ###########################   end   ################################

    def _play_iwalk(self):
        self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
        self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
        ###########################   stats   ##############################
        self.stats['batting'].append(['IBB','']) #base on balls
        self.stats['pitching'].append(['IBB','1']) #base on balls
        ###########################   end   ################################

    def _play_strikeout(self):
        self.main_play = out_in_advance(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play
        self.base = leave_base(self.base, bfrom='B') if not self._is_explicit() else self.base

        ###########################   stats   ##############################
        self.stats['batting'].append(['K','']) #strikeout
        self.stats['fielding'].append(['PO','2']) #strikeout
        self.stats['pitching'].append(['K','1']) #strikeout
        self.stats['batting'].append(['SF',''])  if 'SF' in mpm else None
        self.stats['batting'].append(['SH',''])  if 'SH' in mpm else None
        ###########################   end   ################################

    def _play_pb(self):
        ###########################   stats   ##############################
        self.stats['fielding'].append(['PB','2'])
        ###########################   end   ################################

    def _play_po(self):
        bfrom = mp[2]
        bto = NEXT_BASE[mp[2]]

        self.main_play = out_in_advance(self.main_play, bfrom=bfrom)  if not self._is_explicit(bfrom) else self.main_play
        self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit() else self.base

        ###########################   stats   ##############################
        PO = re.findall('[1-9]\)', mp)
        if PO:
            PO = PO[0].replace(')','')
            self.stats['fielding'].append(['PO',PO[0]])

        As = re.findall('(?:\([^\(]+\))', mp)
        if As:
            As = As[0].replace('(','').replace(')','')
            for a in As:
                if a not in PO:
                    self.stats['fielding'].append(['A',a])

        passes = re.sub('PO[123]\(','', mp).replace(')','').replace('E','')
        self.modifiers['passes'].append(passes)


        self.stats['running'].append(['PO',bfrom, bfrom]) #player never moved base
        ###########################   end   ################################

    def _play_po_error(self):
        ###########################   stats   ##############################
        bfrom = mp[2]
        bto = NEXT_BASE[mp[2]]
        self.stats['running'].append(['PO(E)',bfrom, bto])
        As = re.findall('^(?:\([1-9]+E)+', mp) #assists to other players
        if As:
            As = As[0].replace('E','').replace('(','')
            for a in As:
                self.stats['fielding'].append(['A',a])

        passes = re.sub('PO[123]\(','', mp).replace(')','').replace('E','')
        self.modifiers['passes'].append(passes)

        error_fielder = re.findall('E[1-9]', mp)[0]
        self.stats['fielding'].append(['E',error_fielder[1]])
        ###########################   end   ################################

    def _play_pocs(self):
        for split in mp.split(';'):
            if split[0:2] == 'CS':
                bto = split[2]
                bfrom = PREVIOUS_BASE[split[2]]
                self.main_play = out_in_advance(self.main_play, bto=bto) if not self._is_explicit(bfrom) else self.main_play
                self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit() else self.base
                self.stats['running'].append(['CS',bfrom, bto])
            else:
                bto = split[4]
                bfrom = PREVIOUS_BASE[split[4]]
                out_in_advance( self.main_play, bto=bto) if not self._is_explicit(bfrom) else self.main_play  #there are CS events together with POCS
                self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit() else self.base
                self.stats['running'].append(['CS',bfrom, bto])

            ###########################   stats   ##############################

            PO = re.findall('[1-9]\)', split)
            if PO:
                PO = PO[0].replace(')','')
                self.stats['fielding'].append(['PO',PO[0]])

            As = re.findall('(?:\([^\(]+\))', split)
            if As:
                As = As[0].replace('(','').replace(')','')
                for a in As:
                    if a not in PO:
                        self.stats['fielding'].append(['A',a])

            passes = re.sub('POCS[123]\(','', mp).replace(')','').replace('E','')
            self.modifiers['passes'].append(passes)
            ###########################   end   ################################

    def _play_pocs_error(self):
        ###########################   stats   ##############################
        bto = mp[4]
        bfrom = PREVIOUS_BASE[mp[4]]
        self.stats['running'].append(['CS(E)',bfrom, bto])

        As = re.findall('^(?:\([1-9]+E)+', mp) #assists to other players
        if As:
            As = As[0].replace('E','').replace('(','')
            for a in As:
                self.stats['fielding'].append(['A',a])

        error_fielder = re.findall('E[1-9]', mp)[0]
        self.stats['fielding'].append(['E',error_fielder[1]])

        passes = re.sub('POCS[123]\(','', mp).replace(')','').replace('E','')
        self.modifiers['passes'].append(passes)
        ###########################   end   ################################

    def _play_single(self):
        self.main_play = advance_base(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play
        self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
        ###########################   stats   ##############################
        self.stats['batting'].append(['1B','']) #single
        self.stats['batting'].append(['H','']) #hit
        self.stats['pitching'].append(['H','1'])

        passes = re.findall('[0-9]', mp)
        if passes:
            self.modifiers['passes'].append(passes[0])
        ###########################   end   ################################

    def _play_stolen_base(self):
        for sb in mp.split(';'):
            if sb[0:2] == 'SB':
                bto = sb[2]
                bfrom = PREVIOUS_BASE[sb[2]]
                self.main_play = advance_base(self.main_play, bto=sb[2]) if not self._is_explicit(bfrom) else self.main_play
                self.base = move_base(self.base, bfrom=bfrom, bto=bto) if not self._is_explicit(bfrom) else self.base #B-1 except if explicily moving on advances
                ###########################   stats   ##############################
                self.stats['running'].append(['SB',bfrom, bto])
                self.stats['running'].append(['R',bfrom, bto]) if sb[2] == 'H' else None
                ###########################   end   ################################

    def _play_triple(self):
        self.main_play = advance_base(self.main_play, bfrom='B', bto='3')  if not self._is_explicit() else self.main_play
        self.base = move_base(self.base, bfrom='B', bto='3') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
        ###########################   stats   ##############################
        self.stats['batting'].append(['3B',''])
        self.stats['batting'].append(['H','']) #hit

        passes = re.findall('[0-9]', mp)
        if passes:
            self.modifiers['passes'].append(passes[0])
        ###########################   end   ################################

    def _play_wp(self):
        ###########################   stats   ##############################
        self.stats['pitching'].append(['WP','1'])
        ###########################   end   ################################

    def _play_ci(self):
        if 'E1' in mpm :
            ###########################   stats   ##############################
            self.stats['fielding'].append(['E','1'])
            ###########################   end   ################################
        elif 'E2' in mpm:
            ###########################   stats   ##############################
            self.stats['fielding'].append(['CI','2'])
            ###########################   end   ################################
        elif 'E3' in mpm:
            ###########################   stats   ##############################
            self.stats['fielding'].append(['E','3'])
            ###########################   end   ################################



    def _main_play(self, mp, mpm):
        """Parse main play"""

        if mp == '99': #error or unknown --> usually out
            self.main_play =  out_in_advance(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play#at bat is out
            self.base = leave_base(self.base, bfrom='B') if not self._is_explicit() else self.base

        elif re.findall('^[1-9]', mp) and not re.findall('\(', mp) and not re.findall('E', mp):

            #single out, or without multiple plays

            if 'FO' not in mpm:
                self.main_play =  out_in_advance(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play#at bat is out
                self.base = leave_base(self.base, bfrom='B') if not self._is_explicit() else self.base

            if 'FO' in mpm and not re.findall('B', mp):
                self.main_play = advance_base(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play #B-1 except if explicily moving on advances
                self.base = move_base(self.base, bfrom='B', bto='1')

            PO = mp[-1]
            As = mp[:-1]
            if As:
                for a in As: self.stats['fielding'].append(['A',a])

            self.stats['batting'].append(['SF',''])  if 'SF' in mpm else None
            self.stats['batting'].append(['SH',''])  if 'SH' in mpm else None
            self.stats['batting'].append(['GDP',''])  if 'GDP' in mpm else None

            passes = re.sub('(?:\([^\)]+\))','',mp)
            self.modifiers['passes'].append(passes)


        elif re.findall('^[1-9](?:[1-9]*(?:\([B123]\))?)*\+?\-?$', mp): # implicit B out or not

            for base_out in re.findall('(?:\([B123]\))', mp):
                expression = '[\-]{0}'.format(base_out[1])
                moves = self.str.split('.')[len(self.str.split('.'))-1]
                if not re.findall(expression, self.str.split('.')[len(self.str.split('.'))-1]) and base_out[1] not in self.move_on_error: #a player moved to that base in advaances
                    self.main_play = out_in_advance(self.main_play, bfrom=base_out[1]) #excluding at bat
                    self.base = leave_base(self.base, bfrom=base_out[1])
                else:
                    self.main_play['out'] += 1
                    #self.base = leave_base(self.base, bfrom=base_out[1])

            if 'FO' in mpm and not re.findall('B', mp):
                self.main_play = advance_base(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play #B-1 except if explicily moving on advances
                self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base


            #Testing for double play
            double_play = False
            triple_play = False

            if 'BGDP' in mpm or 'BPDP' in mpm or 'DP' in mpm or 'FDP'in mpm or 'GDP' in mpm or 'LDP' in mpm:
                double_play = True

            if 'BGTP' in mpm or 'BPTP' in mpm or 'TP' in mpm or 'FTP' in mpm or 'GTP' in mpm or 'LTP' in mpm:
                triple_play = True

            if double_play and not re.findall('B', mp) and (self.main_play['out'] + self.ad_out) == 2:
            #   E.G: 5(2)4(1)/GDP --> b advanced to first
                self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
                self.base = move_base(self.base, bfrom='B',bto='1') if not self._is_explicit() else self.base

            if not double_play and not re.findall('B', mp):
            #   E.G.: 16(1)/F
                self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
                self.base = move_base(self.base, bfrom='B',bto='1') if not self._is_explicit() else self.base

            if double_play and self.main_play['out'] + self.ad_out < 2:
                if 'FO' not in mpm:
                    self.main_play =  out_in_advance(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play#at bat is out
                    self.base = leave_base(self.base, bfrom='B') if not self._is_explicit() else self.base
                else:
                    self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base


            if triple_play and self.main_play['out'] + self.ad_out < 3:
                if 'FO' not in mpm:
                    self.main_play =  out_in_advance(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play#at bat is out
                    self.base = leave_base(self.base, bfrom='B') if not self._is_explicit() else self.base
                else:
                    self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base

            ###########################   stats   ##############################
            fielder1 = re.findall('^[1-9]$', mp) #flyball, not always present
            fielders2 = re.findall('[1-9]\(', mp)#$$()$ play, with explicit outs
            fielders2 = [x.replace('(','') for x in fielders2] if fielders2 else []
            fielders3 = re.findall('^[1-9][1-9]+$', mp) #when its a sequence and out
            fielders3 = [fielders3[0][-1]] if fielders3 else []
            fielders4 = [mp[-1]] if re.findall('[1-9]$', mp) and 'GDP' in mpm  else [] #it was a Ground into Double Play

            POs = fielder1 + fielders2 + fielders3 + fielders4

            double_play = False
            triple_play = False

            if 'BGDP' in mpm or 'BPDP' in mpm or 'DP' in mpm or 'FDP'in mpm or 'GDP' in mpm or 'LDP' in mpm:
                double_play = True

            if 'BGTP' in mpm or 'BPTP' in mpm or 'TP' in mpm or 'FTP' in mpm or 'GTP' in mpm or 'LTP' in mpm:
                triple_play = True

            for po in POs:
                self.stats['fielding'].append(['PO',po[0]])
                self.stats['fielding'].append(['DP',po[0]]) if double_play else None
                self.stats['fielding'].append(['TP',po[0]]) if triple_play else None

            all_fielders_touched = re.sub(r'\([^)]*\)', '', mp)
            for fielder in all_fielders_touched:
                if fielder not in POs:
                    self.stats['fielding'].append(['A',fielder])


            self.stats['batting'].append(['SF',''])  if 'SF' in mpm else None
            self.stats['batting'].append(['SH',''])  if 'SH' in mpm else None
            self.stats['batting'].append(['GDP',''])  if 'GDP' in mpm else None

            passes = re.sub('(?:\([^\)]+\))','',mp)
            self.modifiers['passes'].append(passes)
            ###########################   end   ##############################

        elif re.findall('^[1-9][1-9]*E[1-9]*$', mp): #error on out, B-1 implicit if not explicit
            self.main_play = advance_base(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play #B-1 except if explicily moving on advances
            self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances

            ###########################   stats   ##############################
            error_fielder = re.findall('E[1-9]$', mp)[0]
            self.stats['fielding'].append(['E',error_fielder[1]])
            ###########################   end   ##############################

        elif re.findall('^CS[23H](?:\([1-9]+\))+', mp):##caught stealing (except errors):
            for cs in mp.split(';'):
                bto = cs[2]
                bfrom = PREVIOUS_BASE[cs[2]]

                if re.findall('[\-X]{0}'.format(bfrom), self.str.split('.')[len(self.str.split('.'))-1]):

                    self.main_play['out'] += 1
                else:

                    self.main_play = out_in_advance(self.main_play, bto=cs[2])
                    self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit(bfrom) else self.base

                ###########################   stats   ##############################
                self.stats['running'].append(['CS',bfrom, bto])

                PO = re.findall('[1-9]\)', cs)
                if PO:
                    PO = PO[0].replace(')','')
                    self.stats['fielding'].append(['PO',PO[0]])

                As = re.findall('(?:\([^\(]+\))', cs)
                if As:
                    As = As[0].replace('(','').replace(')','')
                    for a in As:
                        if a not in PO:
                            self.stats['fielding'].append(['A',a])

                passes = re.sub('CS[23H]','', cs).replace('(','').replace(')','').replace('E','')
                if passes:
                    self.modifiers['passes'].append(passes)
                ###########################   end   ################################

        elif re.findall('^CS[23H](?:\([1-9]*E[1-9]+)+', mp): ## caught stealing errors
            #the advance could also be explicit given the error, for more than one base.
            for cs in mp.split(';'):
                bto = cs[2]
                bfrom = PREVIOUS_BASE[cs[2]]

                if not self._is_explicit(bfrom):
                    if re.findall('[\-X]{0}'.format(bfrom), self.str.split('.')[len(self.str.split('.'))-1]):
                        self.main_play[bto] = 1
                        if bto == 'H' or bfrom == '3':
                            self.main_play['run'] += 1

                        if bto=='H':
                            self.base[bto].append(self.base[bfrom])
                        else:
                            self.base[bto] = self.base[bfrom]

                    else:
                        self.main_play = advance_base(self.main_play, bto=bto)
                        self.base = move_base(self.base, bfrom=bfrom, bto=bto)

                ###########################   stats   ##############################
                self.stats['running'].append(['CS(E)',bfrom, bto]) #caught stealing w error

                As = re.findall('^(?:\([1-9]+E)+', cs)
                if As:
                    As = As[0].replace('E','').replace('(','')
                    for a in As:
                        self.stats['fielding'].append(['A',a])


                error_fielder = re.findall('E[1-9]', cs)[0]
                self.stats['fielding'].append(['E',error_fielder[1]])

                passes = re.sub('CS[23H]','', cs).replace('(','').replace(')','').replace('E','')
                if passes:
                    self.modifiers['passes'].append(passes)
                ###########################   end   ################################


        elif re.findall('^BK$', mp):# balk (batter remains but all other get one base)

            ###########################   stats   ##############################
            self.stats['pitching'].append(['BK','1'])
            ###########################   end   ################################

        elif re.findall('^D[0-9]*\??$', mp): #double
            self.main_play = advance_base(self.main_play, bto='2',bfrom='B') if not self._is_explicit() else self.main_play
            self.base = move_base(self.base, bfrom='B', bto='2') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            self.stats['batting'].append(['2B',''])
            self.stats['batting'].append(['H','']) #hit
            self.stats['pitching'].append(['H','1'])

            passes = re.findall('[0-9]', mp)
            if passes:
                self.modifiers['passes'].append(passes[0])
            ###########################   end   ################################

        elif re.findall('^DGR[0-9]*$', mp): #ground rule double (two bases for everyone as ball went out after being in)
            self.main_play = advance_base(self.main_play, bto='2',bfrom='B')  if not self._is_explicit() else self.main_play
            self.base = move_base(self.base, bfrom='B', bto='2') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            self.stats['batting'].append(['DGR',''])
            self.stats['batting'].append(['H','']) #hit
            self.stats['pitching'].append(['H','1'])

            passes = re.findall('[0-9]+', mp)
            if passes:
                self.modifiers['passes'].append(passes[0])
            ###########################   end   ################################

        elif re.findall('^DI$', mp): #defensive indifference

            ###########################   stats   ##############################
            for explicit_move in self.em:
                bto = explicit_move[0][2]
                bfrom = explicit_move[0][0]
                self.stats['running'].append(['DI',bfrom, bto])
            ###########################   end   ################################

        elif re.findall('^E[1-9]+\??$', mp): ## error allowing batter to get on base (B-1 implicit or not)

            if not re.findall('K', self.mp[0]): #it is an error but not on second event following strike
                self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
                self.base = move_base(self.base, bfrom='B',bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            error_fielder = re.findall('E[1-9]$', mp)[0]
            if 'TH' in mpm: #throwing error
                self.stats['fielding'].append(['E(TH)',error_fielder[1]])
            else:
                self.stats['fielding'].append(['E',error_fielder[1]])

            passes = re.findall('[0-9]+', mp)
            if passes:
                self.modifiers['passes'].append(passes[0])
            ###########################   end   ################################

        elif re.findall('^FC[1-9]?\??$',mp):# fielders choice (also implicit B-1)
            self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
            self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            self.stats['batting'].append(['FC',''])
            if len(mp) > 2:
                self.stats['fielding'].append(['FC',mp[2]])
                self.modifiers['passes'].append(mp[2])
            ###########################   end   ################################

        elif re.findall('^FLE[1-9]+$',mp): # error on foul fly play (error given to the play but no advances)

            ###########################   stats   ##############################
            self.stats['fielding'].append(['FLE',mp[3]])
            ###########################   end   ################################

        elif re.findall('^H[R]?[1-9]*[D]?$', mp): #home run
            self.main_play = advance_base(self.main_play, bto='H',bfrom='B')  if not self._is_explicit() else self.main_play
            self.base = move_base(self.base, bfrom='B', bto='H') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            self.stats['running'].append(['R','B', 'H'])

            self.stats['batting'].append(['HR','']) #home run
            self.stats['pitching'].append(['HR','1'])

            self.stats['batting'].append(['H','']) #hit
            self.stats['pitching'].append(['H','1'])

            self.stats['batting'].append(['R','']) #run

            if 'IPHR' in mpm:
                self.stats['batting'].append(['IPHR',''])
            ###########################   end   ################################


        elif re.findall('^HP$', mp): #hit by pitch
            self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
            self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            self.stats['batting'].append(['HBP','']) #hit by pitch
            ###########################   end   ################################

        elif re.findall('^W[^P]',mp) or mp=='W': # walk
            self.main_play = advance_base(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play
            self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            self.stats['batting'].append(['BB','']) #base on balls
            self.stats['pitching'].append(['BB','1']) #base on balls
            ###########################   end   ################################

        elif re.findall('^I[W]?',mp): # intentional walk
            self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
            self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            self.stats['batting'].append(['IBB','']) #base on balls
            self.stats['pitching'].append(['IBB','1']) #base on balls
            ###########################   end   ################################

        elif re.findall('^K',mp): #strikeout
            self.main_play = out_in_advance(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play
            self.base = leave_base(self.base, bfrom='B') if not self._is_explicit() else self.base

            ###########################   stats   ##############################
            self.stats['batting'].append(['K','']) #strikeout
            self.stats['fielding'].append(['PO','2']) #strikeout
            self.stats['pitching'].append(['K','1']) #strikeout
            self.stats['batting'].append(['SF',''])  if 'SF' in mpm else None
            self.stats['batting'].append(['SH',''])  if 'SH' in mpm else None
            ###########################   end   ################################

        elif re.findall('^NP$',mp): #no play
            pass

        elif re.findall('^(?:OA)?(?:99)?$',mp): #unkown play
            pass

        elif re.findall('^PB$', mp): #passed ball
            #will keep any advancement to explicit for now. Othersie uncomment below
            #self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
            #self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            self.stats['fielding'].append(['PB','2'])
            ###########################   end   ################################

        elif re.findall('^PO[123](?:\([1-9]+\))',mp): #picked off of base (without error)
            bfrom = mp[2]
            bto = NEXT_BASE[mp[2]]

            if re.findall('[\-X]{0}'.format(bfrom), self.str.split('.')[len(self.str.split('.'))-1]):
                self.main_play['out'] += 1
            else:
                self.main_play = out_in_advance(self.main_play, bto=bto)  if not self._is_explicit(bfrom) else self.main_play
                self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit(bfrom) else self.base

            #self.main_play = out_in_advance(self.main_play, bfrom=bfrom)  if not self._is_explicit(bfrom) else self.main_play
            #self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit(bfrom) else self.base

            ###########################   stats   ##############################
            PO = re.findall('[1-9]\)', mp)
            if PO:
                PO = PO[0].replace(')','')
                self.stats['fielding'].append(['PO',PO[0]])

            As = re.findall('(?:\([^\(]+\))', mp)
            if As:
                As = As[0].replace('(','').replace(')','')
                for a in As:
                    if a not in PO:
                        self.stats['fielding'].append(['A',a])

            passes = re.sub('PO[123]\(','', mp).replace(')','').replace('E','')
            self.modifiers['passes'].append(passes)


            self.stats['running'].append(['PO',bfrom, bfrom]) #player never moved base
            ###########################   end   ################################

        elif re.findall('^PO[123](?:\([1-9]*E[1-9]+)',mp): #pick off with pass error (no out nothing implicit)

            ###########################   stats   ##############################
            bfrom = mp[2]
            bto = NEXT_BASE[mp[2]]
            self.stats['running'].append(['PO(E)',bfrom, bto])
            As = re.findall('^(?:\([1-9]+E)+', mp) #assists to other players
            if As:
                As = As[0].replace('E','').replace('(','')
                for a in As:
                    self.stats['fielding'].append(['A',a])

            passes = re.sub('PO[123]\(','', mp).replace(')','').replace('E','')
            self.modifiers['passes'].append(passes)

            error_fielder = re.findall('E[1-9]', mp)[0]
            self.stats['fielding'].append(['E',error_fielder[1]])
            ###########################   end   ################################

        elif re.findall('^POCS[23H](?:\([1-9]+\))',mp): #POCS%($$) picked off off base % (2, 3 or H) with the runner charged with a caught stealing

            for split in mp.split(';'):
                if split[0:2] == 'CS':
                    bto = split[2]
                    bfrom = PREVIOUS_BASE[split[2]]

                    if re.findall('[\-]{0}'.format(bfrom), self.str.split('.')[len(self.str.split('.'))-1]) or bfrom in self.move_on_error:
                        self.main_play['out'] += 1
                    else:
                        self.main_play = out_in_advance(self.main_play, bto=bto)  if not self._is_explicit(bfrom) else self.main_play
                        self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit(bfrom) else self.base

                    #self.main_play = out_in_advance(self.main_play, bto=bto) if not self._is_explicit(bfrom) else self.main_play
                    #self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit(bfrom) else self.base


                    self.stats['running'].append(['CS',bfrom, bto])
                else:
                    bto = split[4]
                    bfrom = PREVIOUS_BASE[split[4]]

                    if re.findall('[\-]{0}'.format(bfrom), self.str.split('.')[len(self.str.split('.'))-1]) or bfrom in self.move_on_error:
                        self.main_play['out'] += 1
                    else:
                        self.main_play = out_in_advance(self.main_play, bto=bto)  if not self._is_explicit(bfrom) else self.main_play
                        self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit(bfrom) else self.base

                    #out_in_advance( self.main_play, bto=bto) if not self._is_explicit(bfrom) else self.main_play  #there are CS events together with POCS
                    #self.base = leave_base(self.base, bfrom=bfrom) if not self._is_explicit(bfrom) else self.base

                    self.stats['running'].append(['CS',bfrom, bto])

                ###########################   stats   ##############################

                PO = re.findall('[1-9]\)', split)
                if PO:
                    PO = PO[0].replace(')','')
                    self.stats['fielding'].append(['PO',PO[0]])

                As = re.findall('(?:\([^\(]+\))', split)
                if As:
                    As = As[0].replace('(','').replace(')','')
                    for a in As:
                        if a not in PO:
                            self.stats['fielding'].append(['A',a])

                passes = re.sub('POCS[123]\(','', mp).replace(')','').replace('E','')
                self.modifiers['passes'].append(passes)
                ###########################   end   ################################

        elif re.findall('^POCS[23H](?:\([1-9]*E[1-9]+)',mp):#POCS errors

            for split in mp.split(';'):
                bto = split[4]
                bfrom = PREVIOUS_BASE[split[4]]

                if not self._is_explicit(bfrom):
                    if re.findall('[\-]{0}'.format(bfrom), self.str.split('.')[len(self.str.split('.'))-1]) or bfrom in self.move_on_error:
                        self.main_play[bto] = 1
                        if bto == 'H' or bfrom == '3':
                            self.main_play['run'] += 1

                        if bto=='H':
                            self.base[bto].append(self.base[bfrom])
                        else:
                            self.base[bto] = self.base[bfrom]

                    else:
                        self.main_play = advance_base(self.main_play, bto=bto)
                        self.base = move_base(self.base, bfrom=bfrom, bto=bto)


                #self.base = move_base(self.base, bfrom=bfrom, bto=bto) if not self._is_explicit(bfrom) else self.base
                #self.advances = advance_base(self.advances, bfrom=bfrom, bto=bto) if not self._is_explicit(bfrom) else self.advances

            ###########################   stats   ##############################
            bto = mp[4]
            bfrom = PREVIOUS_BASE[mp[4]]
            self.stats['running'].append(['CS(E)',bfrom, bto])

            As = re.findall('^(?:\([1-9]+E)+', mp) #assists to other players
            if As:
                As = As[0].replace('E','').replace('(','')
                for a in As:
                    self.stats['fielding'].append(['A',a])

            error_fielder = re.findall('E[1-9]', mp)[0]
            self.stats['fielding'].append(['E',error_fielder[1]])

            passes = re.sub('POCS[123]\(','', mp).replace(')','').replace('E','')
            self.modifiers['passes'].append(passes)
            ###########################   end   ################################

        elif re.findall('^S[0-9]*\??\+?$',mp): #single
            self.main_play = advance_base(self.main_play, bfrom='B') if not self._is_explicit() else self.main_play
            self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            self.stats['batting'].append(['1B','']) #single
            self.stats['batting'].append(['H','']) #hit
            self.stats['pitching'].append(['H','1'])

            passes = re.findall('[0-9]', mp)
            if passes:
                self.modifiers['passes'].append(passes[0])
            ###########################   end   ################################

        elif re.findall('^SB[23H]',mp): #stolen base
            sbs = []
            for sb in mp.split(';'):
                if sb[0:2] == 'SB':
                    sbs.append(sb)

            sbs.sort(key = lambda item: (['1','2','3','H'].index(item[2]), item), reverse=True)

            for sb in sbs:
                bto = sb[2]
                bfrom = PREVIOUS_BASE[sb[2]]

                if not self._is_explicit(bfrom):
                    #check if explicit moved, so wont zero out the base left
                    if re.findall('[\-]{0}'.format(bfrom), self.str.split('.')[len(self.str.split('.'))-1]) or bfrom in self.move_on_error:
                        self.main_play[bto] = 1
                        if bto == 'H' or bfrom == '3':
                            self.main_play['run'] += 1

                        if bto=='H':
                            self.base[bto].append(self.base[bfrom])
                        else:
                            self.base[bto] = self.base[bfrom]


                    else:
                        self.main_play = advance_base(self.main_play, bto=sb[2])
                        self.base = move_base(self.base, bfrom=bfrom, bto=bto)


                ###########################   stats   ##############################
                self.stats['running'].append(['SB',bfrom, bto])
                self.stats['running'].append(['R',bfrom, bto]) if sb[2] == 'H' else None
                ###########################   end   ################################

        elif re.findall('^T[0-9]*\??\+?$',mp): #triple
            self.main_play = advance_base(self.main_play, bfrom='B', bto='3')  if not self._is_explicit() else self.main_play
            self.base = move_base(self.base, bfrom='B', bto='3') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances
            ###########################   stats   ##############################
            self.stats['batting'].append(['3B',''])
            self.stats['batting'].append(['H','']) #hit

            passes = re.findall('[0-9]', mp)
            if passes:
                self.modifiers['passes'].append(passes[0])
            ###########################   end   ################################

        elif re.findall('^WP', mp): ## wild pitch - base runner advances
            #the advance should only be explicit. If not, uncomment below
            #self.main_play = advance_base(self.main_play, bfrom='B')  if not self._is_explicit() else self.main_play
            #self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base #B-1 except if explicily moving on advances

            ###########################   stats   ##############################
            self.stats['pitching'].append(['WP','1'])
            ###########################   end   ################################

        elif re.findall('^C$', mp): #catcher interference or pitcher or first baseman
            if 'E1' in mpm :
                ###########################   stats   ##############################
                self.main_play = advance_base(self.main_play, bfrom='B', bto='1')  if not self._is_explicit() else self.main_play
                self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base

                self.stats['fielding'].append(['E','1'])
                ###########################   end   ################################
            elif 'E2' in mpm:
                ###########################   stats   ##############################
                self.main_play = advance_base(self.main_play, bfrom='B', bto='1')  if not self._is_explicit() else self.main_play
                self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base

                self.stats['fielding'].append(['CI','2'])
                ###########################   end   ################################
            elif 'E3' in mpm:
                ###########################   stats   ##############################
                self.main_play = advance_base(self.main_play, bfrom='B', bto='1')  if not self._is_explicit() else self.main_play
                self.base = move_base(self.base, bfrom='B', bto='1') if not self._is_explicit() else self.base

                self.stats['fielding'].append(['E','3'])
                ###########################   end   ################################


        else:
            self.log.debug('Main event not known: {0}'.format(mp))
            #raise eventNotFoundError('Event Not Known', mp)


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

        #secondary play
        self.sp = re.findall('(?<=\+)(?:[^\.^\+^/]+)', self.str.split('.')[0])

        #'+' could be a string in a location or a separator of plays (second play)
        if not self.sp:
            self.mpm = re.findall('(?<=/)[^\+^/]+', self.str.split('.')[0].replace('#','').replace('+',''))
        else:
            self.mpm = re.findall('(?<=/)[^\+^/]+', self.str.split('.')[0].split('+')[0].replace('#','').replace('+',''))
        #print ('\nmpm:\t', self.mpm)

        self.mpd = re.findall('(?<=\()(?:[^\)^/])+', self.str.split('.')[0].split('+')[0])
        #print ('\nmpd\t', self.mpd)


        str_spm = self.str.split('.')[0].split('+',1)[1] if len(self.str.split('.')[0].split('+',1)) > 1 else ''
        self.spm = re.findall('(?<=/)(?:[^/^\+]+)', str_spm)
        #print ('\nspm:\t', self.spm)

        #advances:
        self.ea = self.str.split('.')[len(self.str.split('.'))-1].split(';') if len(self.str.split('.'))>1 else []
        self.ea.sort(key = lambda item: (['B','1','2','3'].index(item[0]), item), reverse=True)

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


    def final_moves(self):
        """Combine main play with explicit advances.
        Also, it needs to check to make sure bases are correct based on previous
        play (previous_advances)
        """

        for key, value in self.main_play.items():
            if key in ['out', 'run','H']:
                self.advances[key] += value
            else: #bases
                self.advances[key] = value


    def decipher(self):
        """Parse baseball play
        """
        self.move_on_error = []
        #initialize this play
        self.modifiers = {
            'out': 0,
            'run': 0,
            'bunt': 0,
            'trajectory': '',
            'location': '',
            'interference':'',
            'review': '',
            'foul': 0,
            'force out': 0,
            'throw':0,
            'sacrifice': '',
            'relay':0,
            'other':[],
            'courtesy':'',
            'passes': [],
            'DP': False,
            'TP': False,
        }

        self.stats = {
            'batting': [], #event, player (left blank as batter is contextual)
            'fielding': [], #event, event
            'running':[], #event, base_from, base_to
            'pitching':[], #event, player
            }

        self.main_play={'out': 0,'run': 0}
        #self._initialize_modifiers()

        #take the pieces of hte play (main play, secondary, advances, modifiers, describers)
        self._split_plays()
        mp = self.mp[0].replace('#','').replace('!','').replace('?','')
        mpm= self.mpm

        #read advance first (Explicit moves)
        self._advances()

        #read main play
        self._main_play(mp = mp, mpm=mpm)
        self._modifiers(modifiers = self.mpm)

        #read secondary play if there
        if self.sp:
            sp = self.sp[0].replace('#','').replace('!','').replace('?','')
            spm = self.spm
            self._main_play(mp = sp, mpm=spm)
            self._modifiers(modifiers= self.spm)

        #combine explicit + implicit moves
        self.final_moves()


class eventNotFoundError(Exception):
    """ Exception that is raised when an event is not recognized
    """
    def __init__(self, error, event):
        self.log = logging.getLogger(__name__)
        self.log.debug("Event not found: {0}".format(event))
        super(eventNotFoundError, self).__init__(event)
