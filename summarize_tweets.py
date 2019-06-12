#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 22:15:28 2019

@author: mike
"""


def summarized():
    import pandas as pd
    import re
    import string
    import os
    os.chdir('/home/mike/Analytics/NJ Transit/tweet logs')

    """
    Pull tweets from CSV files
    """
    lines = ['ACRL', 'MBPJ', 'ME', 'MOBO', 'NEC', 'NJCL', 'PVL', 'RVL']
    tweets = pd.DataFrame(columns = ['text', 'time', 'id', 'line'])
    for line in lines:
        temp = pd.read_csv('NJTransit_' + line + '.csv', parse_dates=['time'])
        temp['line'] = line
        tweets = tweets.append(temp)
    tweets = tweets.reset_index(drop=False)
    tweets['date'] = tweets['time'].dt.date
    
    """
    Feature Creation
    """
    tweets['valid'] = tweets['text'].apply(lambda s: 1 if re.search(r'train[ #]*.*from', s.lower() ) else 0)
    relevant = tweets[tweets['valid'] == 1]
    
    relevant['train_prep'] = relevant['text'].apply(lambda s: re.search(r'train[# ,s]*\d*', s.lower() ).group(0) )
    relevant['train'] = relevant['train_prep'].apply(lambda s: re.search(r'\d+', s.lower() ).group(0) if re.search(r'\d', s.lower() ) else 'error')
    relevant = relevant[relevant['train'] != 'error'] # removes ~40 which should have been removed in there in the first place
    
    # Time ... VERY GOOD
    relevant['time_prep'] = relevant['text'].apply(lambda s: re.search(r'(\d|\d\d):\d\d.*?(pm|am)', s.lower() ).group(0) if re.search(r'(\d|\d\d):\d\d.*?(pm|am)', s.lower() ) else 'error' )
    relevant['time_train'] = relevant['time_prep'].apply(lambda s: s.replace(" ", ""))
    relevant['time_train'] = relevant['time_train'].apply(lambda s: re.search(r'.*(\dpm|\dam)', s.lower() ).group(0) if re.search(r'.*(\dpm|\dam)', s.lower() ) else 'error' )
    relevant['temp_len'] = relevant['time_train'].apply(lambda s: len(s))
    relevant = relevant[((relevant['temp_len'] == 6) | (relevant['temp_len'] == 7))]
    
    # Station ... STILL NOT PERFECT
    relevant['station_prep'] = relevant['text'].apply(lambda s: re.search(r'from(.*?)(is|has)', s.lower() ).group(0) if re.search(r'from(.*?)(is|has)', s.lower() ) else 'error' )
    relevant['station_prep'] = relevant['station_prep'].apply(lambda s: s.rsplit(' ', 1)[0])
    relevant['station_prep'] = relevant['station_prep'].apply(lambda s: s.split(' ', 1)[-1].strip())
    relevant['station'] = relevant['station_prep'].apply(lambda s: s.translate(str.maketrans('', '', string.punctuation)) )
    relevant = relevant[relevant['station_prep'] != 'error']
    
    # Cancel or Delay ... VERY GOOD, but didn't actually check
    relevant['Delay'] = relevant['text'].apply(lambda s: 'delay' in s.lower() or 'late' in s.lower() )
    def cancel(row):
        value = ('cancel' in row['text'].lower() ) and (row['Delay'] == False)
        return(value)
    relevant['Cancel'] = relevant.apply(lambda row: cancel(row), axis=1)
    
    # Delay Length...pretty good i think?
    def delay_len(row):
        value = ''
        if row['Delay'] == 1:
            if re.search(r'\d+( min|min| hour|hour| hr|hr)', row['text'].lower() ):
                value = re.search(r'\d+( min|min| hour|hour| hr|hr)', row['text'].lower() ).group(0)
            else: value = 'Unknown' # "An update to follow". Should be careful not to double count!
        return(value)
    relevant['delay_time_prep'] = relevant.apply(lambda row: delay_len(row), axis=1)
    
    def delay_units(row):
        value = None
        multiplier = 1
        if (('hour' in row['delay_time_prep'].lower() )| ('hr' in row['delay_time_prep'].lower() )):
            multiplier = 60
        if ((row['delay_time_prep'] != 'Unknown') & (row['delay_time_prep'] != '')):
            number = int(re.search(r'\d+', row['delay_time_prep'].lower() ).group(0) )
            value  = multiplier * number
        return(value)
    relevant['delay_minutes'] = relevant.apply(lambda row: delay_units(row), axis=1)
    
    # reason = due to {reason} --> need to do further analysis to cluster these
    relevant['reason_text'] = relevant['text'].apply(lambda s: re.search(r'(due to).*', s.lower() ).group(0) if re.search(r'(due to).*', s.lower() ) else 'noreasongiven' )
    relevant['reason_text'] = relevant['reason_text'].apply(lambda s: s.lower().replace("due to", ""))
    
    # Remove hyperlink words
    pattern = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    relevant['reason_text'] = relevant['reason_text'].apply(lambda s: pattern.sub('', s))
    
    # Remove numbers
    relevant['reason_text'] = relevant['reason_text'].apply(lambda s: ''.join([i for i in s if not i.isdigit()]))
    
    
    """
    Remove Unwanted Tweets
    """
    # Non Delay/Cancellations
    relevant = relevant[(relevant['Delay']==1) | (relevant['Cancel']==1)]
    
    # Duplicate Delays/Cancellations
    relevant = relevant.drop_duplicates(subset=['date', 'train'], keep='first')
    
    
    """
    Tokenize and Get/Remove Stopwords
    """
    
    ### Tokenize, remove punctuation ###
    from nltk.tokenize import RegexpTokenizer
    tokenizer = RegexpTokenizer(r'\w+')
    relevant['block'] = relevant['reason_text'].apply(lambda s: tokenizer.tokenize(s))
    
    ### Remove word endings
    from nltk.stem import WordNetLemmatizer 
    lemmatizer = WordNetLemmatizer() 
    relevant['block'] = relevant['block'].apply(lambda words: [lemmatizer.lemmatize(word) for word in words])
    
    ### Get Stopwords
    from nltk.corpus import stopwords
    
    # English stopwords
    swrds = set(stopwords.words('english'))
    
    # Station Stop Names
    import pandas as pd
    stops = pd.read_csv('C:/Users/mikea/Documents/Analytics/NJ Transit/rail_data/'+'stops.csv', names = ['stop_name'])
    stops['keep'] = stops['stop_name'].apply(lambda s: 0 if 'LIGHT RAIL' in s.upper() else 1)
    stops = stops[stops['keep']==1]
    stops['stop_name'].str.lower().str.split().apply(swrds.update)
    swrds.update(['st', 'th', 'nd', 'rd', 'phila', 'philadelphia', 'ht', 'hts', 'nyp', 'nyps', 'psny', 'nps', 'junction', 'ave', 'avenue', 'mills', 'matawan', 'aberdeen', 'morrisville', 'brielle', 'bayhead'])
    
    # Other bad words
    swrds.update(['noreasongiven', 'near', 'update', 'follow', 'bus', 'service', 'provided', 'am', 'pm'])
    
    ### Remove stopwords
    relevant['block'] = relevant['block'].apply(lambda word_list: [word for word in word_list if word not in swrds])
    
    
    """
    Studying Misspellings and Word Freqs
    """
    
    ### Count word frequencies
    from collections import Counter
    word_freqs = Counter(relevant['block'].sum())
    
    # Find all unique words
    all_words = word_freqs.keys()
    
    # Find mis-spellings
    from spellchecker import SpellChecker
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
    
    ### Remove words seen less than 100 times
    relevant['block3'] = relevant['block2'].apply(lambda words: [word for word in words if word_freqs[word] >= 10])
    relevant['block3_alph'] = relevant['block3'].apply(lambda x: sorted(x)) # Order of words doesn't matter
    relevant['reason'] = relevant['block3'].apply(lambda x: ' '.join(x)) # Change list of words into string. Note: Not doing alphabetical this time, so sentences make sense.
    
    ### Create a number for each delay/cancel reason
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
    return relevant, phrases


### Return a df containing counts of each reason code, given the input df
def reason_counts(df, phrases, n):
    import pandas as pd
    reason_counts = pd.DataFrame({'count':df['block_number'].value_counts()})
    reason_counts = reason_counts.reset_index()
    reason_counts['reason'] = reason_counts['index'].apply(lambda x: phrases.get(x))
    reason_counts['reason_str'] = reason_counts['reason'].apply(lambda l: ', '.join(l))
    
    # reason_counts = reason_counts[reason_counts['count'] >= n]
    reason_counts = reason_counts[:10]
    return reason_counts


data, phrases = summarized()
# reason_counts = reason_counts(data, phrases, 10)


#I don't think a topic model is appropriate, because there aren't enough words!
#"""
#Topic Modeling on reason_block
#"""
#
## Create corpus and generate topics
#from gensim import corpora
#dictionary = corpora.Dictionary(relevant['block3'])
#corpus = [dictionary.doc2bow(text) for text in relevant['block3']]
#
#import gensim
#topics = 8
#ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics = topics, id2word=dictionary, passes=15)
#ldamodel.save('model.gensim')
#topics = ldamodel.print_topics(num_words=4)
#for topic in topics:
#    print(topic)
#    
#import pyLDAvis
#lda_display = pyLDAvis.gensim.prepare(ldamodel, corpus, dictionary, sort_topics=False)
#pyLDAvis.save_html(lda_display, 'Topic Model Viz.html')
#
## Assign topic to each HERE


