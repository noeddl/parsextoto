# coding=utf8

##############################################################
#                                                            #
#                       Pars Ex Toto                         #
#                                                            #
#             Created on 23.01.2015 for #clunc15             #
#           by Anett Diesner and Esther Seyffarth            #
#                                                            #
#      (see Twitter Account @parsextoto for output)          #
#                                                            #
##############################################################

import tweepy
import sqlite3
import config
import random
import time

from parsextoto import Parsextoto
    
def login():
    # for info on the tweepy module, see http://tweepy.readthedocs.org/en/v3.1.0/
    
    # Authentication is taken from config.py
    consumer_key = config.consumer_key
    consumer_secret = config.consumer_secret
    access_token = config.access_token
    access_token_secret = config.access_token_secret
    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    
    api = tweepy.API(auth)    
    return api

def post():
    
    #api = login()
    p = Parsextoto()

    while True:            # if you want to tweet without pauses (floods timeline!)
    
    #tweeted = False         # set tweeted to an integer if you want to tweet e.g. 3x in a row
    #while not tweeted:      
        start = time.time()

        p.reset() # needed when generating several sentences
        output = p.get_sentence()

        print(output)
        #api.update_status(output)
                        
        ende = time.time()
        print "%.2f" % (ende - start)
        print '----'
        
        tweeted = True

post()         
#post("parsextoto.sqlite")

