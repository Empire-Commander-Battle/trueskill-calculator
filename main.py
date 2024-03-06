import trueskill
import pandas as pd

import os
import argparse

parser = argparse.ArgumentParser(
    prog='trueskill',
    description='Calculates trueskill scores from record files')


def file_path(path):
    if path != '' and path[-1] != os.sep:
        return path
    raise argparse.ArgumentTypeError(f'{path} is not a valid file path')


def existing_file_path(path):
    if os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(f'{path} does\' exist')


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

df = pd.read_excel(INPUT_FILENAME, header=None, sheet_name='Internal')

rounds_row_pos = (7, 8)
commander_column_pos = (0, 8)

victorious_commander_row = 5
defeated_commander_row = 6

rounds = df.iloc[rounds_row_pos[0]][rounds_row_pos[1]:]
events = list(rounds.index[rounds == 'R1'])
row_end = rounds.index[rounds == 'Type'][-1] + 1

rounds_indexes = [list(range(start, end, 2))
                  for start, end in zip(events + [row_end],
                                        events[1:] + [row_end])]

# sort indexes so they are in chronological order
rounds_indexes = [round_index for event_rounds in reversed(
    rounds_indexes) for round_index in event_rounds]

commanders = df[commander_column_pos[0]][commander_column_pos[1]:]

ratings_history = []
ratings = {}

for round_no, round_index in enumerate(rounds_indexes):
    victor_team = []
    looser_team = []

    draw = False

    victorious_commander = '[COMMANDER]' + df.iloc[victorious_commander_row, round_index]
    defeated_commander = '[COMMANDER]' + df.iloc[defeated_commander_row, round_index]

    victorious_commander_rating = trueskill.Rating()
    if victorious_commander in ratings:
        victorious_commander_rating = ratings[victorious_commander]
    else:
        ratings[victorious_commander] = victorious_commander_rating

    defeated_commander_rating = trueskill.Rating()
    if defeated_commander in ratings:
        defeated_commander_rating = ratings[defeated_commander]
    else:
        ratings[defeated_commander] = defeated_commander_rating

    for player_index in range(commander_column_pos[1],
                              commander_column_pos[1] + commanders.size):
        match df.iloc[player_index, round_index]:
            case 1:
                victor_team.append(commanders[player_index])
            case 0:
                looser_team.append(commanders[player_index])
            case 0.5:
                draw = True
                match df[round_index + 1][player_index][0]:
                    case '1':
                        looser_team.append(commanders[player_index])
                    case '2':
                        victor_team.append(commanders[player_index])

    victor_team_ratings = [
        ratings[i] if i in ratings else trueskill.Rating() for i in victor_team]
    victor_team_ratings.append(victorious_commander_rating)

    looser_team_ratings = [
        ratings[i] if i in ratings else trueskill.Rating() for i in looser_team]
    looser_team_ratings.append(defeated_commander_rating)

    victor_team_ratings, looser_team_ratings = trueskill.rate([victor_team_ratings,
                                                               looser_team_ratings],
                                                              [0, 0] if draw else [0, 1])

    for player, rating in zip(victor_team, victor_team_ratings):
        ratings[player] = rating
    ratings[victorious_commander] = victor_team_ratings[-1]

    for player, rating in zip(looser_team, looser_team_ratings):
        ratings[player] = rating
    ratings[defeated_commander] = looser_team_ratings[-1]

    mu_dict = {}
    sigma_dict = {}

    for player, rating in ratings.items():
        mu_dict[player] = rating.mu
        sigma_dict[player] = rating.sigma

    ratings_history.append((round_no, mu_dict, sigma_dict))

# reverse order
output_dict = {}
for round_no, mu, sigma in reversed(ratings_history):
    output_dict[f'mu{round_no}'] = mu
    output_dict[f'sigma{round_no}'] = sigma

table = pd.DataFrame.from_dict(output_dict)

table.to_excel(OUTPUT_FILENAME)
