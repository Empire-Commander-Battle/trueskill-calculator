import matplotlib.pyplot as plt
import pandas as pd

import os
import argparse

parser = argparse.ArgumentParser(
    prog='trueskill-graph',
    description='Graph trueskill scores')


def file_path(path):
    if path != '' and path[-1] != os.sep:
        return path
    raise argparse.ArgumentTypeError(f'{path} is not a valid file path')


def existing_file_path(path):
    if os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(f'{path} does\' exist')


parser.add_argument('scorefile',
                    type=existing_file_path)
parser.add_argument('outputfile',
                    type=file_path)
parser.add_argument('-d', '--dpi',
                    type=int,
                    default=300)

args = parser.parse_args()

INPUT_FILENAME = args.scorefile
OUTPUT_FILENAME = args.outputfile
DPI = args.dpi

# MAIN

df = pd.read_excel(INPUT_FILENAME)

plt.figure(figsize=(30, 10))

rounds = list(range(df.shape[1]//2, 0, -1))
plt.xticks(rounds)

for player_index in range(df.shape[0]):
    player_name = df.iloc[player_index, 0]

    mu = []
    for round_index in range(1, df.shape[1], 2):
        mu.append(df.iloc[player_index, round_index])

    plt.plot(rounds, mu, label=player_name)

plt.legend(title='Players')

plt.savefig(OUTPUT_FILENAME, dpi=DPI)
