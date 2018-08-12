
import pandas as pd
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import sys

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


def parse_file(year):
    ########################################################################
    ENDPOINT = 'https://www.retrosheet.org/events/'
    EXTENSION = '.zip'
    ########################################################################
    """
    TODO:
        - Parse team files (TEAMYYYY)
    """
    filename = '{0}eve'.format(year)
    resp = urlopen(ENDPOINT + filename+EXTENSION)
    #print (year)
    zipfile = ZipFile(BytesIO(resp.read()))

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

        if file[-3:] == 'ROS': #roster file
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

        #print (file)
        order = 0
        game_id = 0
        version = 0
        for row in zipfile.open(file, 'r').readlines():

            row = row.decode("utf-8")
            #rows.append(row.rstrip('\n'))
            row_type = row.rstrip('\n').split(',')[0]
            #print (row_type)

            if row_type == 'id':
                order = 0
                game_id = row.rstrip('\n').split(',')[1].strip('\r')
                #ids.append(game_id)

            if row_type == 'version':

                version = row.rstrip('\n').split(',')[1].strip('\r')
                #versions.append(version)

            if row_type == 'info':
                if row.rstrip('\n').split(',')[1] != 'save':
                    info_piece = [
                        row.rstrip('\n').split(',')[1],
                        row.rstrip('\n').split(',')[2].strip('\r').strip('"').strip('"')
                    ]
                    infos.append([game_id]+ info_piece)

            if row_type == 'start':
                start_piece = [
                    row.rstrip('\n').split(',')[1],
                    row.rstrip('\n').split(',')[2].strip('"'),
                    row.rstrip('\n').split(',')[3],
                    row.rstrip('\n').split(',')[4],
                    row.rstrip('\n').split(',')[5].strip('\r')
                ]
                starting.append([game_id, version]+start_piece)

            if row_type == 'play':
                play_piece = [
                    row.rstrip('\n').split(',')[1],
                    row.rstrip('\n').split(',')[2],
                    row.rstrip('\n').split(',')[3],
                    row.rstrip('\n').split(',')[4],
                    row.rstrip('\n').split(',')[5],
                    row.rstrip('\n').split(',')[6].strip('\r')
                ]
                plays.append([order, game_id, version] + play_piece)
                order += 1

            if row_type == 'sub':
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
    plays_df = pd.DataFrame(plays, columns = ['order','game_id','version','inning','home_team','player_id','count_on_batter','pitches','play'])

    #comments are not parsed.
    comments_df = pd.DataFrame(comments, columns = ['order','game_id','version','comment'])

    #earned runs for each pitcher.
    er_df = pd.DataFrame(er, columns = ['game_id','version','earned_run','player_id','variable'])

    return games ,starting_df , plays_df, er_df, subs_df, comments_df, rosters_df, teams_df#, ids_df, versions_df



if __name__=='__main__':

    save_to_csv = input('Save files to csv?[y/n]')

    if save_to_csv.lower() == 'y':
        print ('Will save to csv...')

    info_final = pd.DataFrame()
    starting_final = pd.DataFrame()
    plays_final = pd.DataFrame()
    er_final = pd.DataFrame()
    subs_final = pd.DataFrame()
    comments_final = pd.DataFrame()
    rosters_df_final = pd.DataFrame()
    teams_df_final = pd.DataFrame()

    ########################################################################
    yearFrom = 1921
    yearTo = 2017
    ########################################################################
    print ('Downloading Files ... \n')
    for count, year in enumerate(range(yearFrom,yearTo+1,1), 0): #+1 for inclusive
        #print (yea)
        total = yearTo-yearFrom+1
        progress(count, total, status=year)

        infos, starting, plays, er, subs, comments, rosters_df, teams_df = parse_file(year)

        info_final = info_final.append(infos)
        starting_final = starting_final.append(starting)
        plays_final = plays_final.append(plays)
        er_final = er_final.append(er)
        subs_final = subs_final.append(subs)
        comments_final = comments_final.append(comments)
        rosters_df_final = rosters_df_final.append(rosters_df)
        teams_df_final = teams_df_final.append(teams_df)

    progress(100,100, status="\nFiles Downloaded")

    if save_to_csv == 'y':
        print ('Saving to csv...')
        info_final.to_csv('info.csv', index=False)
        starting_final.to_csv('starting.csv', index=False)
        plays_final.to_csv('plays.csv', index=False)
        er_final.to_csv('er.csv', index=False)
        subs_final.to_csv('subs.csv', index=False)
        comments_final.to_csv('comments.csv', index=False)
        rosters_df_final.to_csv('rosters.csv', index=False)
        teams_df_final.to_csv('teams.csv', index=False)
        print ('saved')
