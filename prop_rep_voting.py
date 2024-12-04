import re
import math
import numpy as np
import pandas as pd
from collections import defaultdict

def check_format(df):
    """Check that the dataframe is formatted correctly"""
    positions = set()
    names = set()
    col_name_regex = re.compile('(.*)\s\[(.*)\]')
    for col in df.columns:
        try:
            match = re.match(col_name_regex, col)
            position, name = match.groups()
            positions.add(position)
            names.add(name)
        except:
            continue

    if len(positions) == 0 or len(names) == 0:
        raise ValueError('The specified document is of the incorrect format. '
                         'Column headings must be of the form "Position [Name]".')

    assert df.map(np.isreal).all().all(), "Not all cells contain numbers."

def make_candidate_dictionary():
    """Create dictionary of positions and candidates with empty counts"""
    counts = defaultdict(dict)
    col_name_regex = re.compile('(.*)\s\[(.*)\]')
    cols = votes.columns

    for column in cols:
        # Extract position & candidate name from column name using regex
        try:
            match = re.match(col_name_regex, column)
            position, name = match.groups()
        except:
            continue

        # Add to dictionary of candidates
        counts[position][name] = 0

    return counts

def count_votes(position):
    """Function to count votes according to proportional representation"""
    # Extract only the columns pertaining to the current position
    position_df = votes.filter(like=position + ' [', axis=1)
    round = 1

    while True:
        # Count all first preference votes
        for index, row in position_df.iterrows():
            for candidate in counts[position]:
                if row[f'{position} [{candidate}]'] == 1:
                    counts[position][candidate] += 1
                    row[f'{position} [{candidate}]'] = 0   # set 1st pref to 0 so as not to count again in later rounds
                    break

        print(f'Round {round} results: {counts[position]}')

        # Check if the quota has been reached
        if max(counts[position].values()) >= quota:
            elected = max(counts[position], key=counts[position].get)
            results[position] = elected
            print(f'{elected} is elected as {position} after round {round}.')
            break

        else:
            # Check for a tie in minimum votes
            round_counts = list(counts[position].values())
            if round_counts.count(min(round_counts)) > 1:
                remaining = list(counts[position].keys())
                print(f'!!! Tie for {position} after round {round}. '
                      f'Remaining candidates: {remaining}')
                results[position] = f'Tie – {remaining}'
                break

            # Identify and eliminate the candidate with the fewest votes
            min_candidate = min(counts[position], key=counts[position].get)
            print(f'{min_candidate} is eliminated.')
            counts[position].pop(min_candidate)

            # Adjust DataFrame values: decrease all preference numbers after the eliminated candidate
            for index, row in position_df.iterrows():
                eliminated_pref = row[f'{position} [{min_candidate}]']
                for candidate in counts[position]:
                    if row[f'{position} [{candidate}]'] > eliminated_pref:
                        position_df.at[index, f'{position} [{candidate}]'] -= 1

            round += 1


if __name__ == "__main__":

    # Load votes from a spreadsheet as formatted by Google Forms
    filename = 'sample_votes.csv'
    votes = pd.read_csv(filename)
    votes = votes.drop('Timestamp', axis=1)  # Don't need timestamp
    check_format(votes)

    # Calculate quota
    quota = math.floor(len(votes.index) / 2 + 1)
    print(f'Quota: {quota}')

    counts = make_candidate_dictionary()
    results = {}

    for position in counts.keys():
        print(f'\nCounting {position}...')
        count_votes(position)

    print('\n\n***** Results *****')
    for position in results:
        print(f'{position}: {results[position]}')
