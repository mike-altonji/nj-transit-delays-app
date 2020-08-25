#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 28 20:40:24 2019
Purpose: To collect the most recent Twitter data from NJ Transit accounts.
@author: mike
"""

# Import libraries
import pandas as pd
import tweepy
import yaml
import os

# Load config file containing tokens, secrets and paths
with open('config.yml') as file:
    config = yaml.full_load(file)
consumer_token  = config['CONSUMER_TOKEN']
consumer_secret = config['CONSUMER_SECRET']
access_token    = config['ACCESS_TOKEN']
access_secret   = config['ACCESS_SECRET']
tweet_logs_path = config['TWEET_LOGS_PATH']

# Authentication with Twitter API
auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)


def get_tweets(username, prior_tweets_exist=False, all_tweets=None, since_id=0): 
    """
    Creates/Updates dataframe of Tweets for a given username
    username: Twitter handle to scrape
    prior_tweets_exist: True if there is already a .csv file with Tweets from this username
    all_tweets: The dataframe of all prior Tweets for this username
    since_id: Tweet ID of the most recent Tweet from this username in the locally stored .csv
    """
        
    print(username)
    ### First round of tweet extraction
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
    
    ### Remaining rounds of tweet extraction
    # Stop running program when out of tweets OR reached 3200 tweet limit
    x = 0
    while len(tweets) > 0:
        x+=1
        print(x)
        try:
            # Extract tweets
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


### Pull Tweets from select users, then save.
for name in ['NJTransit', 'NJTransit_ACRL', 'NJTransit_RVL', 'NJTransit_PVL', 'NJTransit_MBPJ', 'NJTransit_MOBO', 'NJTransit_ME', 'NJTransit_NJCL', 'NJTransit_NEC']:
    if os.path.isfile(tweet_logs_path + name + '.csv'):
        prior_tweets = pd.read_csv(tweet_logs_path + name + '.csv')
        last_index = prior_tweets['id'][0]+1
        all_tweets = get_tweets(name, True, prior_tweets, last_index)
    else: 
        print('First time pulling', name)
        all_tweets = get_tweets(name, False, None, None)
    all_tweets.to_csv(tweet_logs_path + name + '.csv', index=False)
