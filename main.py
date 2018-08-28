from retrosheet import Retrosheet
from argparse import ArgumentParser


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("-s", "--start", dest="year_start", help="Start year", type=int)
    parser.add_argument("-e", "--end", dest="year_end", help="End year for the parser", type=int)

    args = parser.parse_args()

    rs = Retrosheet()
    rs.batch_parse(yearFrom=args.year_start, yearTo=args.year_end, batchsize=10)
    
    '''
    rs.get_data(yearFrom=args.year_start, yearTo=args.year_end)
    rs.to_df()
    rs.save_csv(path_str='')
    '''
