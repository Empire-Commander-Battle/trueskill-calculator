import os

def file_path(path):
    if path != '' and path[-1] != os.sep:
        return path
    raise argparse.ArgumentTypeError(f'{path} is not a valid file path')


def existing_file_path(path):
    if os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(f'{path} does\' exist')

rounds_row_pos = (7, 12)
event_type_row_pos = (7, 0)
commander_col_pos = (0, 13)

date_row = 1
victorious_commander_row = 10
defeated_commander_row = 11
survivor_percent_row = 9
