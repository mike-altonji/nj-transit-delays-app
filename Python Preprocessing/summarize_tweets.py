#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 22:15:28 2019
Purpose: To preprocess the raw NJ Transit Twitter data.
   - Provides time, reason, and Train ID of the delay using Regex statements.
@author: mike
"""

# Import libraries
import pandas as pd
import re
import string
import csv
import yaml
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer 
from nltk.corpus import stopwords
from collections import Counter
from spellchecker import SpellChecker

# Load config file containing paths
with open('config.yml') as file:
    config = yaml.full_load(file)
repo_path = config['REPO_PATH']
tweet_logs_path = config['TWEET_LOGS_PATH']
rail_data_path  = config['RAIL_DATA_PATH']


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

#########   Main Function -----------------------------------------------------
def summarized():
    """
    Performs all data preprocessing and cleaning, appropriate for storing in a CSV.
    """
    
    ### Pulls tweets from the CSV files
    lines = ['ACRL', 'MBPJ', 'ME', 'MOBO', 'NEC', 'NJCL', 'PVL', 'RVL']
    tweets = pd.DataFrame(columns = ['text', 'time', 'id', 'line'])
    for line in lines:
        temp = pd.read_csv(tweet_logs_path + 'NJTransit_' + line + '.csv', parse_dates=['time'])
        temp['line'] = line
        tweets = tweets.append(temp)
    tweets = tweets.reset_index(drop=False)
    tweets['date'] = tweets['time'].dt.date
    
    ### Feature Creation
    tweets['valid'] = tweets['text'].apply(lambda s: 1 if re.search(r'train[ #]*.*from', s.lower() ) else 0)
    relevant = tweets[tweets['valid'] == 1]
    
    relevant['train_prep'] = relevant['text'].apply(lambda s: re.search(r'train[# ,s]*\d*', s.lower() ).group(0) )
    relevant['train'] = relevant['train_prep'].apply(lambda s: re.search(r'\d+', s.lower() ).group(0) if re.search(r'\d', s.lower() ) else 'error')
    relevant = relevant[relevant['train'] != 'error'] # removes ~40 which should have been removed in there in the first place
    
    # Extract Time of delay. Very accurate.
    relevant['time_prep'] = relevant['text'].apply(lambda s: re.search(r'(\d|\d\d):\d\d.*?(pm|am)', s.lower() ).group(0) if re.search(r'(\d|\d\d):\d\d.*?(pm|am)', s.lower() ) else 'error' )
    relevant['time_train'] = relevant['time_prep'].apply(lambda s: s.replace(" ", ""))
    relevant['time_train'] = relevant['time_train'].apply(lambda s: re.search(r'.*(\dpm|\dam)', s.lower() ).group(0) if re.search(r'.*(\dpm|\dam)', s.lower() ) else 'error' )
    relevant['temp_len'] = relevant['time_train'].apply(lambda s: len(s))
    relevant = relevant[((relevant['temp_len'] == 6) | (relevant['temp_len'] == 7))]
    
    # Extract Station of delay. Not perfect.
    relevant['station_prep'] = relevant['text'].apply(lambda s: re.search(r'from(.*?)(is|has)', s.lower() ).group(0) if re.search(r'from(.*?)(is|has)', s.lower() ) else 'error' )
    relevant['station_prep'] = relevant['station_prep'].apply(lambda s: s.rsplit(' ', 1)[0])
    relevant['station_prep'] = relevant['station_prep'].apply(lambda s: s.split(' ', 1)[-1].strip())
    relevant['station_raw'] = relevant['station_prep'].apply(lambda s: s.translate(str.maketrans('', '', string.punctuation)) )
    relevant = relevant[relevant['station_prep'] != 'error']
    
    # Determine if Cancellation or Delay. Very accurate.
    relevant['Delay'] = relevant['text'].apply(lambda s: 'delay' in s.lower() or 'late' in s.lower() )
    def cancel(row):
        """
        Checks if the train stoppage is a cancellation or a delay
        """
        value = ('cancel' in row['text'].lower() ) and (row['Delay'] == False)
        return(value)
    relevant['Cancel'] = relevant.apply(lambda row: cancel(row), axis=1)
    
    # Determine delay Length. Very accurate.
    def delay_len(row):
        """
        Find duration of the delay
        """
        value = ''
        if row['Delay'] == 1:
            if re.search(r'\d+( min|min| hour|hour| hr|hr)', row['text'].lower() ):
                value = re.search(r'\d+( min|min| hour|hour| hr|hr)', row['text'].lower() ).group(0)
            else: value = 'Unknown' # "An update to follow" Tweets cause issues. Should be careful not to double count.
        return(value)
    relevant['delay_time_prep'] = relevant.apply(lambda row: delay_len(row), axis=1)
    
    def delay_units(row):
        """
        Checks if delay is reported in minutes or hours
        """
        value = None
        multiplier = 1
        if (('hour' in row['delay_time_prep'].lower() )| ('hr' in row['delay_time_prep'].lower() )):
            multiplier = 60
        if ((row['delay_time_prep'] != 'Unknown') & (row['delay_time_prep'] != '')):
            number = int(re.search(r'\d+', row['delay_time_prep'].lower() ).group(0) )
            value  = multiplier * number
        return(value)
    relevant['delay_minutes'] = relevant.apply(lambda row: delay_units(row), axis=1)
    
    # Extracts reason for delay. (ie "due to {reason}"). Need to cluster these better.
    relevant['reason_text'] = relevant['text'].apply(lambda s: re.search(r'(due to).*', s.lower() ).group(0) if re.search(r'(due to).*', s.lower() ) else 'noreasongiven' )
    relevant['reason_text'] = relevant['reason_text'].apply(lambda s: s.lower().replace("due to", ""))
    
    # Remove hyperlinks
    pattern = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    relevant['reason_text'] = relevant['reason_text'].apply(lambda s: pattern.sub('', s))
    
    # Remove numbers
    relevant['reason_text'] = relevant['reason_text'].apply(lambda s: ''.join([i for i in s if not i.isdigit()]))
    
    ### Remove Unwanted Tweets: Duplicates and those not pertaining to delays/cancellations
    # Non Delay/Cancellations
    relevant = relevant[(relevant['Delay']==1) | (relevant['Cancel']==1)]
    
    # Duplicate Delays/Cancellations
    relevant = relevant.drop_duplicates(subset=['date', 'train'], keep='first')
    
    ### Tokenize and Get/Remove Stopwords
    # Tokenize, remove punctuation
    tokenizer = RegexpTokenizer(r'\w+')
    relevant['block'] = relevant['reason_text'].apply(lambda s: tokenizer.tokenize(s))
    
    # Remove word endings
    lemmatizer = WordNetLemmatizer() 
    relevant['block'] = relevant['block'].apply(lambda words: [lemmatizer.lemmatize(word) for word in words])    
    
    # English stopwords
    swrds = set(stopwords.words('english'))
    
    # Station Stop Names
    stops = pd.read_csv(rail_data_path + 'stops.csv', names = ['stop_name'])
    stops['keep'] = stops['stop_name'].apply(lambda s: 0 if 'LIGHT RAIL' in s.upper() else 1)
    stops = stops[stops['keep']==1]
    stops['stop_name'].str.lower().str.split().apply(swrds.update)
    swrds.update(['st', 'th', 'nd', 'rd', 'phila', 'philadelphia', 'ht', 'hts', 'nyp', 'nyps', 'psny', 'nps', 'junction', 'ave', 'avenue', 'mills', 'matawan', 'aberdeen', 'morrisville', 'brielle', 'bayhead'])
    
    # Other unwanted words
    swrds.update(['noreasongiven', 'near', 'update', 'follow', 'bus', 'service', 'provided', 'am', 'pm'])
    
    # Remove stopwords
    relevant['block'] = relevant['block'].apply(lambda word_list: [word for word in word_list if word not in swrds])
    
    
    ### Studying Misspellings and Word Freqs    
    # Count word frequencies
    word_freqs = Counter(relevant['block'].sum())
    
    # Find all unique words
    all_words = word_freqs.keys()
    
    # Find mis-spellings
    spell = SpellChecker()
    misspelled = spell.unknown(all_words)
    other_valid_words = ['conrail', 'delair']
    [misspelled.remove(word) for word in other_valid_words]
    
    # Manual spell correction, for specific ones
    manual_spell_correction = {'custo':'customer', 'cust':'customer', 'availa':'available', 'availabil':'availability', 'congest':'congestion', 'equipm':'equipment'}
    def spell_corrector(word, corrections):
        if word in corrections: word = corrections[word]
        return word
    relevant['block2'] = relevant['block'].apply(lambda words: [spell_corrector(word, manual_spell_correction) for word in words])
    
    auto_spell_correction = dict()
    for word in misspelled:
        if word not in ['custo', 'cust', 'availa', 'availabil', 'congest', 'equipm']:
            corrected = spell.correction(word)
            auto_spell_correction.update({word:corrected})
    relevant['block2'] = relevant['block2'].apply(lambda words: [spell_corrector(word, auto_spell_correction) for word in words])
    
    # Update word frequencies after spell correction
    word_freqs = Counter(relevant['block2'].sum())
    
    # Remove words seen less than 100 times
    relevant['block3'] = relevant['block2'].apply(lambda words: [word for word in words if word_freqs[word] >= 10])
    relevant['block3_alph'] = relevant['block3'].apply(lambda x: sorted(x)) # Order of words doesn't matter
    relevant['reason'] = relevant['block3'].apply(lambda x: ' '.join(x)) # Change list of words into string. Note: Not doing alphabetical this time, so sentences make sense.
    
    # Create a number for each delay/cancel reason
    list_number = list()
    phrases = dict()
    phrase_id = 0
    for row in range(len(relevant)):
        phrase = relevant['block3_alph'].iloc[row]
        if phrase not in phrases.values():
            list_number.append(phrase_id)
            phrases.update({phrase_id:phrase})
            phrase_id += 1
        else: list_number.append(list(phrases.keys())[list(phrases.values()).index(phrase)])
    relevant['block_number'] = list_number
    
    # Fix the Station Names
    stations = []
    with open(repo_path + 'valid_stations.csv', 'r') as f:
        reader = csv.reader(f)
        lst = list(reader)
    for station in lst:
        stations.append(station[0])
    station_df = relevant['station_raw'].value_counts().reset_index()
    station_df['station'] = station_df['index'].apply(lambda x: right_station(x, stations))
    relevant = relevant.merge(station_df, how = 'left', left_on = 'station_raw', right_on = 'index')
    relevant = relevant[['text', 'id', 'line', 'date', 'train', 'time_train', 'Delay', 'Cancel', 'delay_minutes', 'reason', 'block_number', 'station']]
    return relevant, phrases


def reason_counts(df, phrases, n):
    """
    Return a dataframe containing counts of each reason code
    """
    reason_counts = pd.DataFrame({'count':df['block_number'].value_counts()})
    reason_counts = reason_counts.reset_index()
    reason_counts['reason'] = reason_counts['index'].apply(lambda x: phrases.get(x))
    reason_counts['reason_str'] = reason_counts['reason'].apply(lambda l: ', '.join(l))    
    # reason_counts = reason_counts[reason_counts['count'] >= n]
    reason_counts = reason_counts[:10]
    return reason_counts

### Run data cleaning, save results
data, phrases = summarized()
data.to_csv(repo_path + 'data.csv', index=False)
