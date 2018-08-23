# encoding: utf-8
import sys

PREVIOUS_BASE  = {'H':'3','3':'2','2':'1','1':'B'}
NEXT_BASE  = {'B':'1','1':'2','2':'3','3':'H'}

def out_in_advance(play_dict, bto=None, bfrom=None):
    """runner out when advancing by next base
    - play_dict: play dictionary
    - bto : base to, heading to
    - bfrom: base coming from, previous base
    """
    bto = '1' if not bto and not bfrom else bto
    if bto:
        play_dict[PREVIOUS_BASE[bto]] = 0
        play_dict['out'] += 1
        return play_dict
    play_dict[bfrom] = 0
    play_dict['out'] += 1
    return play_dict


def advance_base(play_dict, bto=None, bfrom=None):
    """runner advanced to next base
    - play_dict: play dictionary
    - bto : base to, heading to
    - bfrom: base coming from, previous base
    """
    bto = '1' if not bto and not bfrom else bto
    if bto == 'H' or bfrom == '3':
        play_dict['run'] += 1
    if bto and not bfrom:
        play_dict.update(dict(zip([PREVIOUS_BASE[bto],bto],(0,1))))
    elif bfrom and not bto:
        play_dict.update(dict(zip([bfrom,NEXT_BASE[bfrom]],(0,1))))
    else: #bto and bfrom explicit
        play_dict.update(dict(zip([bfrom,bto],(0,1))))
    return play_dict

def progress(count, total, status=''):
    """
    Adapted from https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
    """
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[{0}] {1}{2} ... {3}\r'.format(bar, percents, '%', status))
    sys.stdout.flush()
    if count  == total:
        print ('')


def position_name(position_number):
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
    if position_number in position_dic:
        return position_dic[position_number]
    return position_number


def field_conditions(string):
    """
    fieldcond: dry, soaked, wet, unknown;
    precip: drizzle, none, rain, showers, snow, unknown;
    sky: cloudy, dome, night, overcast, sunny, unknown;
    winddir: fromcf, fromlf, fromrf, ltor, rtol, tocf, tolf, torf, unknown;
    temp: (0 is unkown)
    windspeed: (-1 is unkown)
    """
    pass
