#!/usr/bin/env python3
import trueskill
import pandas as pd

import re

import argparse

from shared import *

parser = argparse.ArgumentParser(
    prog='trueskill',
    description='Calculates trueskill scores from record files')

parser.add_argument('recordfile',
                    type=existing_file_path)
parser.add_argument('scorefile', type=file_path)

args = parser.parse_args()

INPUT_FILENAME = args.recordfile
OUTPUT_FILENAME = args.scorefile

# MAIN

# adjust trueskill to 1000
env = trueskill.TrueSkill(mu=1000, sigma=1000/3)
env.make_as_global()

df = pd.read_excel(INPUT_FILENAME, header=None, sheet_name='All', dtype=str)

rounds_row = df.iloc[rounds_row_pos[1], rounds_row_pos[0]:]

rounds_mask = rounds_row.apply(lambda x: isinstance(x, str) and re.match('^R\d$', x) is not None)
rounds_indexes = rounds_row.index[rounds_mask]
rounds_indexes = list(reversed(rounds_indexes))

for last_index in range(commander_col_pos[1], df.iloc[:, commander_col_pos[0]].size):
    if isinstance(df.iloc[last_index, commander_col_pos[0]], str):
        continue
    break

commanders = df.iloc[commander_col_pos[1]:last_index, commander_col_pos[0]]

ratings_history = {}
ratings = {}

# helper class because fuck multiple variables
class Commander:
    def __init__(self, player_name, get_rating_f):
        self.name = 'COMMANDER|' + player_name
        self.player_name = player_name
        self.rating = get_rating_f(self.name)

for round_no, round_index in enumerate(rounds_indexes):
    event_type = df.iloc[event_type_row_pos[1], round_index]

    if event_type not in ratings:
        ratings[event_type] = {}

    def get_rating(name):
        if name in ratings[event_type]:
            return ratings[event_type][name]

        return trueskill.Rating()

    def set_rating(name, rating):
        ratings[event_type][name] = rating

    victor_team = []
    looser_team = []

    draw = False
    blacklist = []

    victorious_commander = None
    if isinstance(df.iloc[victorious_commander_row, round_index], str):
        victorious_commander = Commander(df.iloc[victorious_commander_row, round_index], get_rating)
        blacklist.append(victorious_commander.player_name)

    defeated_commander = None
    if isinstance(df.iloc[defeated_commander_row, round_index], str):
        defeated_commander = Commander(df.iloc[defeated_commander_row, round_index], get_rating)
        blacklist.append(defeated_commander.player_name)

    for player_index in range(commander_col_pos[1],
                              commander_col_pos[1] + commanders.size):
        player_name = df.iloc[player_index, commander_col_pos[0]]
        if player_name in blacklist or df.iloc[player_index, round_index] == '?':
            continue

        match df.iloc[player_index, round_index - 1]:
            case '1':
                victor_team.append(player_name)
            case '0':
                looser_team.append(player_name)
            case '0.5':
                draw = True
                match df.iloc[player_index, round_index][0]:
                    case '1':
                        looser_team.append(player_name)
                    case '2':
                        victor_team.append(player_name)

    victor_team_ratings = [get_rating(i) for i in victor_team]

    if victorious_commander is not None:
        victor_team_ratings.append(victorious_commander.rating)

    looser_team_ratings = [get_rating(i) for i in looser_team]

    if defeated_commander is not None:
        looser_team_ratings.append(defeated_commander.rating)

    victor_team_ratings, looser_team_ratings = trueskill.rate([victor_team_ratings,
                                                               looser_team_ratings],
                                                              [0, 0] if draw else [0, 1])

    for player, rating in zip(victor_team, victor_team_ratings):
        set_rating(player, rating)

    if victorious_commander is not None:
        set_rating(victorious_commander.name, victor_team_ratings[-1])

    for player, rating in zip(looser_team, looser_team_ratings):
        set_rating(player, rating)

    if defeated_commander is not None:
        set_rating(defeated_commander.name, looser_team_ratings[-1])

    mu_dict = {}
    sigma_dict = {}

    for player, rating in ratings[event_type].items():
        mu_dict[player] = rating.mu
        sigma_dict[player] = rating.sigma

    if event_type not in ratings_history:
        ratings_history[event_type] = []
    ratings_history[event_type].append((round_no, mu_dict, sigma_dict))

tables = {}
for event_type, history in ratings_history.items():
    output_dict = {}

    # reverse order
    for round_no, mu, sigma in reversed(history):
        output_dict[f'mu{round_no}'] = mu
        output_dict[f'sigma{round_no}'] = sigma

    table = pd.DataFrame.from_dict(output_dict)
    table.sort_values(f'mu{history[-1][0]}', inplace=True, ascending=False)

    tables[event_type] = table

with pd.ExcelWriter(OUTPUT_FILENAME) as writer:
    for event_type, table in tables.items():
        table.to_excel(writer, sheet_name=event_type)
