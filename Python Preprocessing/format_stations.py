# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 20:14:29 2019
Purpose: To ensure proper labeling of train station names
@author: mikea
"""

# Import libraries
import csv
import pandas as pd
import yaml

# Load config containing paths
with open('config.yml') as file:
    config = yaml.full_load(file)
repo_path = config['REPO_PATH']

def ldist(s1, s2):
    """
    Finds the textual distance between two strings.
    In our case, it is a comparison between a set of pre-existing station names
    versus raw station names in tweets. Allows for misspelled station names.
    """
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def right_station(text, stations):
    """
    Matches known station names to raw station names from tweets.
    Leverages 'ldist' function to make string comparisons, but also contains
    some heuristic logic based on common station abbreviations.
    """
    if text in ['hob', 'nyps', 'nps', 'sec', 'aberdeen', 'matawan']:
        if text == 'hob': selection = 'hoboken'
        elif text == 'nyps': selection = 'psny'
        elif text == 'nps': selection = 'newark penn station'
        elif text == 'sec': selection = 'secaucus'
        elif text in ['matawan', 'aberdeen']: selection = 'aberdeenmatawan'
        else: selection = 'Error'
    else:    
        minimum = 999999999
        selection = 'None'
        for station in stations:
            value = ldist(text, station)
            if value < minimum:
                minimum = value
                selection = station
    return selection

# Create CSV File containing all valid station names
stations = []
with open(repo_path + 'valid_stations.csv', 'r') as f:
    reader = csv.reader(f)
    lst = list(reader)
for station in lst:
    stations.append(station[0])

# Create CSV File containing all mappings of misspelt to correct station names, for manual validation
wrongs = []
with open(repo_path + 'testing.csv', 'r') as f:
    reader = csv.reader(f)
    lst = list(reader)
for wrong in lst:
    wrongs.append(wrong[0])

check = []
for wrong in wrongs:
    check.append([wrong, right_station(wrong, stations)])

## Computes accuracy of station name predictions based on manual labelling
#station_df = pd.read_csv(repo_path + 'Station_Names.csv')
#station_df['Pred'] = station_df['Station'].apply(lambda x: right_station(x, stations))
#station_df['good'] = station_df['Actual'] == station_df['Pred']
#correct_pct = station_df[station_df['good'] == True]['Count'].sum() / station_df['Count'].sum()
