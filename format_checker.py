import pandas as pd
import re

import colorama as cr
import pprint

import enum

import os
import argparse

from shared import *

parser = argparse.ArgumentParser(
    prog='trueskill-recordfile-check',
    description='Checks validity of trueskill record file')

parser.add_argument('recordfile',
                    type=existing_file_path)

parser.add_argument('-v', '--verbose',
                    action='store_true')

args = parser.parse_args()

INPUT_FILENAME = args.recordfile
VERBOSE = args.verbose

# CLASSES

class FormatException(Exception):
    def __init__(self, reason, data = {}):
        self.reason  = reason
        self.data = data
        super().__init__(reason)

def parametize_exception_class(cls, to_add):
    class FormatException(cls):
        def __init__(self, reason, data = {}):
            tmp = {k:v for k,v in to_add.items()}

            for k,v in data.items():
                tmp[k] = v

            super().__init__(reason, tmp)

    return FormatException

def print_format_exception(expt):
    print(cr.Fore.YELLOW + f'REASON: {cr.Fore.WHITE}{e.reason}')
    for name, val in e.data.items():
        print(cr.Fore.MAGENTA + f'{name}: ' + cr.Style.RESET_ALL, end='')
        pprint.pprint(val)

class Check:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        if VERBOSE:
            print(cr.Fore.BLUE + f'{self.name} check: ', end='')

    def __exit__(self, exc_type, exc_value, ext_tb):
        if VERBOSE:
            if exc_type is None:
                print(cr.Fore.GREEN + 'PASSED')
            else:
                print(cr.Fore.RED + 'FAILED')

def print_warning(msg):
    print(cr.Fore.YELLOW + f'WARNING: {msg}')

class Result(enum.Enum):
    UNDEF = 0
    TEAM1_WIN = 1
    TEAM2_WIN = 2
    DRAW = 3

    @classmethod
    def team_to_result(cls, team):
        match team:
            case 1:
                return cls.TEAM1_WIN
            case 2:
                return cls.TEAM2_WIN

    @classmethod
    def team_to_opposite_result(cls, team):
         match team:
            case 1:
                return cls.TEAM2_WIN
            case 2:
                return cls.TEAM1_WIN

# MAIN

alph = list(map(chr, range(ord('A'), ord('Z') + 1)))

def to_abc(x):
    result = ''
    while x != 0:
        res = x % 25
        if res == 0:
            res = 25
        result = alph[res - 1] + result
        x -= res
        x //= 25
    return result

try:
    df = pd.read_excel(INPUT_FILENAME, header=None, sheet_name='All', dtype=str)

    rounds_row = df.iloc[rounds_row_pos[1], rounds_row_pos[0]:]

    rounds_mask = rounds_row.apply(lambda x: isinstance(x, str) and re.match('^R\d+$', x) is not None)
    rounds_indexes = list(rounds_row.index[rounds_mask])

    with Check('at least one round'):
        if len(rounds_indexes) == 0:
            raise FormatException('couldn\'t find any rounds')

    for last_index in range(commander_col_pos[1], df.iloc[:, commander_col_pos[0]].size):
        if isinstance(df.iloc[last_index, commander_col_pos[0]], str):
            continue
        break

    commanders = df.iloc[commander_col_pos[1]:last_index, commander_col_pos[0]]

    with Check('commander uniqueness'):
        tmp = commanders.value_counts()
        tmp = tmp[tmp>=2]

        if tmp.size != 0:
            raise FormatException('non unique commanders',
                                  {'repeating commanders': tmp})

    last_round_passed = True
    last_event_type = None
    last_round_no = None

    round_exceptions = []

    for last_round_index, round_index in zip([rounds_indexes[0] - 2] + rounds_indexes, rounds_indexes):
        try:
            RoundException = parametize_exception_class(FormatException,
                                                        {'round index': to_abc(round_index)})

            with Check('space'):
                if round_index - last_round_index < 2:
                    raise RoundException('need at least 1 cell space between rounds',
                                        {'last round index': last_round_index})

            with Check('date'):
                date = df.iloc[date_row, round_index]
                if not isinstance(date, str):
                    raise RoundException('date is empty',)

            event_type = df.iloc[event_type_row_pos[1], round_index]

            with Check('event type'):
                if not isinstance(event_type, str):
                    raise RoundException('event type is empty')

            name = df.iloc[rounds_row_pos[1], round_index]
            round_no = int(name[1:])

            if last_round_passed:
                with Check('consecutiveness'):
                    if event_type == last_event_type and round_no - last_round_no != -1:
                        raise RoundException('there is gap between round numbers',
                                             {'event type': event_type,
                                              'last event type': last_event_type,
                                              'round no': round_no,
                                              'last round no': last_round_no})
            else:
                print_warning('skipping consecutivness check due to last round not passing')

            victorious_commander = df.iloc[victorious_commander_row, round_index]
            if not isinstance(victorious_commander, str):
                victorious_commander = None

            defeated_commander = df.iloc[defeated_commander_row, round_index]
            if not isinstance(defeated_commander, str):
                defeated_commander = None

            victor_team = []
            looser_team = []

            round_result = Result.UNDEF

            for player_index in range(commander_col_pos[1],
                                    commander_col_pos[1] + commanders.size):
                player_name = df.iloc[player_index, commander_col_pos[0]]

                PlayerException = parametize_exception_class(RoundException,
                                                            {'player index': player_index + 1,
                                                            'player name': player_name})

                data = df.iloc[player_index, round_index]
                if not isinstance(data, str):
                    continue

                if data == '?':
                    continue

                with Check('data format'):
                    if len(data) < 1:
                        raise PlayerException('data is empty string')

                with Check('team'):
                    if data[0] != '1' and data[0] != '2':
                        raise PlayerException('data doesn\'t start with proper team number - 1 or 2',
                                            {'data': data})

                team_no = int(data[0])

                round_result_in = Result.UNDEF
                with Check('W/L check'):
                    value = df.iloc[player_index, round_index - 1]
                    match value:
                        case '1':
                            round_result_in = Result.team_to_result(team_no)
                            victor_team.append(player_name)
                        case '0':
                            round_result_in = Result.team_to_opposite_result(team_no)
                            looser_team.append(player_name)
                        case '0.5':
                            round_result_in = Result.DRAW
                            match team_no:
                                case 1:
                                    looser_team.append(player_name)
                                case 2:
                                    victor_team.append(player_name)
                        case _:
                            raise PlayerException('W/L cell with invalid value',
                                                {'value': value})

                with Check('round result'):
                    if round_result == Result.UNDEF:
                        round_result = round_result_in
                    else:
                        if round_result != round_result_in:
                            raise PlayerException('conflicting victory inference',
                                                {'round result': round_result,
                                                'infered round result': round_result_in})

            with Check('Victorious commander on looser team'):
                if victorious_commander is not None and victorious_commander in looser_team:
                    raise RoundException('victorious commander is on looser team',
                                        {'victor team': victor_team,
                                        'looser team': looser_team,
                                        'victorious commander': victorious_commander,
                                        'defeated commander': defeated_commander})

            with Check('Defeated commander on victor team'):
                if defeated_commander is not None and defeated_commander in victor_team:
                    raise RoundException('victorious commander is on looser team',
                                        {'victor team': victor_team,
                                        'looser team': looser_team,
                                        'victorious commander': victorious_commander,
                                        'defeated commander': defeated_commander})

            with Check('Victor team player number'):
                if len(victor_team) == 0 and victorious_commander == None:
                    raise RoundException('victor team does have no players',
                                        {'victor team': victor_team,
                                        'looser team': looser_team,
                                        'victorious commander': victorious_commander,
                                        'defeated commander': defeated_commander})

            with Check('Looser team player number'):
                if len(looser_team) == 0 and defeated_commander == None:
                    raise RoundException('looser team does have no players',
                                        {'victor team': victor_team,
                                        'looser team': looser_team,
                                        'victorious commander': victorious_commander,
                                        'defeated commander': defeated_commander})

            last_event_type = event_type
            last_round_no = round_no
            last_round_passed = True
        except FormatException as e:
            last_round_passed = False
            round_exceptions.append(e)

    if len(round_exceptions) == 0:
        print(cr.Fore.GREEN + 'FILE PASSED SUECSSFULLY')
    else:
        for e in round_exceptions:
            print_format_exception(e)

except FormatException as e:
    print_format_exception(e)
finally:
    print(cr.Style.RESET_ALL, end='')
