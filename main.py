from retrosheet import Parser

if __name__ == '__main__':
    parser = Parser()
    info, starting, plays, er, subs, comments, rosters, teams = parser.parse_years(yearFrom=1921, yearTo=2017, save_to_csv=True)
