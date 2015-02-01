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

start = time.clock()

def login():
    # Authentication is taken from config.py
    consumer_key = config.consumer_key
    consumer_secret = config.consumer_secret
    access_token = config.access_token
    access_token_secret = config.access_token_secret
    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    
    # Establishing API session
    api = tweepy.API(auth)
    print api.me().name
    return api


def post(path):
    
    #data = getData(path)
    #print len(data)
    api = login()
    
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c1 = conn.cursor()
    c2 = conn.cursor()
    
    
    
    
    # DEMO
    #while True:
    #for i in range(20):
    tweeted = False
    while not tweeted: 
        
        row = c.execute("select * from Substring where Score > 0 order by random() limit 1").fetchone()
        

        longID = row[0]
        shortID = row[1]
        get_longword = 'select * from Wort where WortID = %d' % (longID)
        longword = c1.execute(get_longword).fetchone()[1]

        get_shortword = 'select * from Wort where WortID = %d' % (shortID)
        shortword = c2.execute(get_shortword).fetchone()[1]
         


        long_query = 'select features from Morph where WortID = %d' % (longID)
        long_features = c.execute(long_query).fetchone()[0]
        short_query = 'select features from Morph  where WortID = %d' % (shortID)
        short_features = c.execute(short_query).fetchone()[0]
        #print short_features

        
        query = 'select POS from Wort where WortID = %d' % (shortID)
        short_pos = c.execute(query).fetchone()[0]
        
        #print(long_features, short_features, short_pos)
 
    
        noun_patterns = {u"Masc_Nom_Sg":["Kein %s ohne %s!", "Kein %s ohne %s.", ],
                         u"Neut_Nom_Sg":["Es gibt kein %s ohne %s.", "Kein %s ohne %s!", "Kein %s ohne %s...", ],
                         u"Fem_Nom_Sg":["Undenkbar: Eine %s ohne %s!",u"Was wäre eine %s ohne %s?"]} 
        

        
        verb_patterns = {u"Masc_Nom_Sg":["Jeder %s %s."],
                         u"Fem_Nom_Sg":["Jede %s %s."],
                         u"Fem_Nom_Pl":["Alle %s %s."],
                         u"Masc_Nom_Pl":["Alle %s %s."],
                         u"Neut_Nom_Pl":["Alle %s %s."],
                         u"Masc_Dat_Pl":["Das wichtigste am %s ist das %s."]}
        
        adj_patterns = {u"Masc_Nom_Sg":["Ist jeder %s auch %s?"],
                        u"Fem_Nom_Sg":["Welche %s ist nicht %s?"],
                        u"Neut_Nom_Sg":["Wann ist ein %s %s?"],
                        u"Masc_Nom_Pl":["Sind alle %s auch %s?", "Gibt es %s, die nicht %s sind?", "Nicht alle %s sind auch %s."],
                        u"Fem_Nom_Pl":["Sind alle %s auch %s?", "Gibt es %s, die nicht %s sind?", "Nicht alle %s sind auch %s."],
                        u"Neut_Nom_Pl":["Sind alle %s auch %s?", "Gibt es %s, die nicht %s sind?", "Nicht alle %s sind auch %s."]}                
                        
    
        output = "error"
        
        # high priority output pattern
        if longword.lower().endswith(shortword.lower()):
            if long_features.startswith(u"Masc") and short_features.startswith(u"Masc"):
                output = "Jeder %s ist auch nur ein %s." % (longword, shortword)
            elif long_features.startswith(u"Fem") and short_features.startswith(u"Fem"):
                output = "Jede %s ist auch nur eine %s." % (longword, shortword)
            elif long_features.startswith(u"Neut") and short_features.startswith(u"Neut"):
                output = "Jedes %s ist auch nur ein %s." % (longword, shortword) 
                
        # lower priority output patterns         
        else:              
            if short_pos == u"NN":
                if long_features in noun_patterns:
                    output = noun_patterns[long_features][random.randint(0,len(noun_patterns[long_features])-1)] % (longword, shortword)
                    #output = "error" 
                     
            elif short_pos == u"ADJ":
                if long_features in adj_patterns:
                    if short_features.endswith("Invar") or long_features.split("_",1)[0]+"_Nom" in short_features:
                        output = adj_patterns[long_features][random.randint(0,len(adj_patterns[long_features])-1)] % (longword, shortword) 
            elif short_pos == u"V":   
                if (long_features.endswith("_Pl") and short_features.startswith("3_Pl")) or (long_features.endswith("_Sg") and short_features.startswith("3_Sg")):         
    #             if long_features in verb_patterns:
                    output = verb_patterns[long_features][random.randint(0,len(verb_patterns[long_features])-1)] % (longword, shortword) 
                #output = "error"    # dealing with verbs is complicated
             
        #print(output)   
        if output != "error":
            print(output)
            #api.update_status(output)
            
            # mark combination as already posted
            update = 'UPDATE substring set posted=1 where WortID = %d and SubstringID = %d' % (longID, shortID)
            success = c.execute(update)
            if success:
                conn.commit()
            tweeted = True
                
                
            #raw_input()
        
            

post("parsextoto.sqlite")

print(time.clock()-start)