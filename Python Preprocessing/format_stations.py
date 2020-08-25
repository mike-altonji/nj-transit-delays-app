# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 20:14:29 2019
Purpose: To ensure proper labeling of train station names
@author: mikea
"""


def ldist(s1, s2):
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


import csv
stations = []
with open('C:/Users/mikea/Documents/Analytics/NJ Transit/'+'valid_stations.csv', 'r') as f:
    reader = csv.reader(f)
    lst = list(reader)
for station in lst:
    stations.append(station[0])


wrongs = []
with open('C:/Users/mikea/Documents/Analytics/NJ Transit/'+'testing.csv', 'r') as f:
    reader = csv.reader(f)
    lst = list(reader)
for wrong in lst:
    wrongs.append(wrong[0])

check = []
for wrong in wrongs:
    check.append([wrong, right_station(wrong, stations)])

import pandas as pd
station_df = pd.read_csv('C:/Users/mikea/Documents/Analytics/NJ Transit/'+'Station_Names.csv')
station_df['Pred'] = station_df['Station'].apply(lambda x: right_station(x, stations))
station_df['good'] = station_df['Actual'] == station_df['Pred']
correct_pct = station_df[station_df['good'] == True]['Count'].sum() / station_df['Count'].sum()
