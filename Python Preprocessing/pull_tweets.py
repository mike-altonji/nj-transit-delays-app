#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 28 20:40:24 2019
@author: mike
"""

### Known Issues ###
# 1) SOMETHING IS BROKEN WITH ACRL...IT KEEPS DOING MULTIPLE PULLS EVEN WHEN NO NEW DATA

import os
import pandas as pd
import tweepy

os.chdir('C:/Users/mikea/Documents/Analytics/NJ Transit/tweet logs/')

"""
Authentication with Twitter API
"""
consumer_token      = 'tCn2W8cUblljmfrPjAn2kIxSo'
consumer_secret     = 'awCpenhw5Im0XwMXziZ9CkjRjZizeUgfhm1paq2HAS9zHJkKaJ'
access_token        = '1583849995-uGq8RVAV5V3BGqOWYWgJ8VdMzMtuOuHYz6s4MNb'
access_secret       = 'SX0KK8mLtWd3nxPWn9ySeuPPd6bapAMLE4QK3bBevubsu'

auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)


"""  
Function to extract tweets 
"""
def get_tweets(username, prior_tweets_exist = False, all_tweets = None, since_id = 0): 
    print(username)
    ### Get first round of tweets
    # Extract tweets
    if prior_tweets_exist == False:
        tweets = api.user_timeline(screen_name = username, count = 200, tweet_mode='extended') 
        # Lists for tweet text, date
        tweet_text = [tweet.full_text for tweet in tweets]
        tweet_time = [tweet.created_at for tweet in tweets]
        tweet_id = [tweet.id for tweet in tweets]
        last_id = tweets[-1].id - 1
        all_tweets = pd.DataFrame(data = {'text': tweet_text, 'time': tweet_time, 'id': tweet_id})
    else: 
        tweets  = all_tweets # To make length work
        last_id = None
    # Stop running program when out of tweets OR reached 3200 tweet limit
    x = 0
    while len(tweets) > 0:
        x+=1
        print(x)
        try:
            tweets = api.user_timeline(screen_name = username, count = 200, max_id = last_id, since_id = since_id, tweet_mode='extended')
            # Lists for tweet text, date
            tweet_text = [tweet.full_text for tweet in tweets]
            tweet_time = [tweet.created_at for tweet in tweets]
            tweet_id = [tweet.id for tweet in tweets]
            last_id = tweets[-1].id - 1
            all_tweets = all_tweets.append(pd.DataFrame(data = {'text': tweet_text, 'time': tweet_time, 'id': tweet_id}))        
        except: None
    all_tweets = all_tweets.sort_values(by = 'id', ascending = False)
    all_tweets = all_tweets.drop_duplicates(subset = 'id')
    return(all_tweets) 


"""
Pull Tweets from select users, then save.
"""
for name in ['NJTransit', 'NJTransit_ACRL', 'NJTransit_RVL', 'NJTransit_PVL', 'NJTransit_MBPJ', 'NJTransit_MOBO', 'NJTransit_ME', 'NJTransit_NJCL', 'NJTransit_NEC']:
    if os.path.isfile(name + '.csv'):
        prior_tweets = pd.read_csv(name + '.csv')
        last_index = prior_tweets['id'][0]+1
        all_tweets = get_tweets(name, True, prior_tweets, last_index)
    else: 
        print('First time pulling', name)
        all_tweets = get_tweets(name, False, None, None)
    all_tweets.to_csv(name + '.csv', index=False)
    
    