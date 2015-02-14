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


def post(path):
    
    api = login()
    
    # establishing connection to database that contains our vocabulary etc.
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c1 = conn.cursor()
    c2 = conn.cursor()
    

    #while True:            # if you want to tweet without pauses (floods timeline!)
    
    tweeted = False         # set tweeted to an integer if you want to tweet e.g. 3x in a row
    while not tweeted:      
        
        # retrieving word pairs
        row = c.execute("select * from Substring where posted = 0 order by random() limit 1").fetchone()        # any pair of words
        #row = c.execute("select * from Substring where Score >= 1 and posted = 0 order by random() limit 1").fetchone()        # any pair of words
        #row = c.execute('select * from Substring where SubstringID in (select WortID from Morph where features like "%Masc%" or features like "%Fem%" or features like "%Neut%") and Score >= 1 and posted = 0 order by random() limit 1').fetchone()       # only pairs of NN + NN        
        #row = c.execute('select * from Substring where SubstringID in (select WortID from Morph where features like "%pos%") and Score >= 1 and posted = 0 order by random() limit 1').fetchone()       # only pairs of NN + ADJ
        #row = c.execute('select * from Substring where SubstringID in (select WortID from Morph where features like "3%Pres_Ind") and Score >= 1 and posted = 0 order by random() limit 1').fetchone()       # only pairs of NN + verb
        
        """
        TODO:
        
        - konkretere SQLITE-Abfragen formulieren, um genau die Infos zu haben, die man braucht
            - POS mit aus der DB holen
            - sofort nach DB Anfrage die cases NN/ADJ/V abfragen und alles weitere davon abhängig ausführen
            - ggf bei jedem Aufruf ein NN-ADJ, NN-NN und NN-V Paar holen, mit Abstand von 1 Minute?        
        
        - alle möglichen Features für jedes Wort holen, damit alles vielseitiger wird (Behandlung des Genitivs, weitere
          bisher nicht beachtete Features)
		    - Was bedeutet das Feature Masc_Dat_Sg_OLD?
		    
	    - zuerst entscheiden, welche Art von Satz gebildet werden soll, dann die passenden Einträge aus der DB holen
	      (sollte die Kasus- und Genusprobleme lösen, die zB hier auftreten:
	      https://twitter.com/parsextoto/status/562604744649490432
	      https://twitter.com/parsextoto/status/562958850224312321 )
		    
        """
        
        longID = row[0]
        shortID = row[1]
        get_longword = 'select * from Wort where WortID = %d' % (longID)
        longword = c1.execute(get_longword).fetchone()[1]
        get_shortword = 'select * from Wort where WortID = %d' % (shortID)
        shortword = c2.execute(get_shortword).fetchone()[1]

        # retrieving morphological info for each word
        long_query = 'select features from Morph where WortID = %d' % (longID)
        long_features = c.execute(long_query).fetchone()[0]
        short_query = 'select features from Morph  where WortID = %d' % (shortID)
        short_features = c.execute(short_query).fetchone()[0]        
        query = 'select POS from Wort where WortID = %d' % (shortID)
        short_pos = c.execute(query).fetchone()[0]
        
        # defining sentences, according to morphological info of longer word    
        noun_patterns = {u"Masc_Nom_Sg":["Kein %s ohne %s!", "Kein %s ohne %s.", ],
                         u"Neut_Nom_Sg":["Es gibt kein %s ohne %s.", "Kein %s ohne %s!", "Kein %s ohne %s...", ],
                         u"Fem_Nom_Sg":["Undenkbar: Eine %s ohne %s!",u"Was wäre eine %s ohne %s?"]} 
        
        # TODO: add sentences for plural nouns
        
        rev_noun_patterns = {u"Masc_Nom_Sg":["Wie kommt der %s in den %s?"],
                             u"Neut_Nom_Sg":["Wie kommt das %s ins %s?"],
                             u"Fem_Nom_Sg":["Wie kommt die %s in die %s?"],
                             u"Masc_Nom_Pl":["Was macht der %s in den %s?"],
                             u"Neut_Nom_Pl":["Was macht das %s in den %s?"],
                             u"Fem_Nom_Pl":["Was macht die %s in den %s?"],
                             }
        
        # reverse sentences to make more interesting
        verb_patterns = {u"Masc_Nom_Sg":["Jeder %s %s."],
                         u"Fem_Nom_Sg":["Jede %s %s."],
                         u"Fem_Nom_Pl":["Alle %s %s."],
                         u"Masc_Nom_Pl":["Alle %s %s."],
                         u"Neut_Nom_Pl":["Alle %s %s."]}
                         # u"Masc_Dat_Pl":["Das wichtigste am %s ist das %s."]}    # something wrong with this sentence
        
        # too many questions
        adj_questions = {u"Masc_Nom_Sg":["Ist jeder %s %s?"],
                        u"Fem_Nom_Sg":["Welche %s ist nicht %s?"],
                        u"Neut_Nom_Sg":["Wann ist ein %s %s?"],
                        u"Masc_Nom_Pl":["Sind alle %s %s?", "Gibt es %s, die nicht %s sind?"],
                        u"Fem_Nom_Pl":["Sind alle %s %s?", "Gibt es %s, die nicht %s sind?"],
                        u"Neut_Nom_Pl":["Sind alle %s %s?", "Gibt es %s, die nicht %s sind?"]} 
        
        adj_patterns = {u"Masc_Nom_Sg":["Jeder %s ist %s."],
                        u"Fem_Nom_Sg":["Jede %s ist %s!"],
                        u"Neut_Nom_Sg":["Ein %s ist immer %s!"],
                        u"Masc_Nom_Pl":["Nicht alle %s sind %s.", "Alle %s sind %s!"],
                        u"Fem_Nom_Pl":["Nicht alle %s sind %s.", "Alle %s sind %s!"],
                        u"Neut_Nom_Pl":["Nicht alle %s sind %s.", "Alle %s sind %s!"]}
        
                                               
    
        output = u"Was wäre ein Bot ohne Fehler?"        # "default" output
        
        # high priority output pattern
        if longword.lower().endswith(shortword.lower()):        
            if long_features.startswith(u"Masc") and short_features.startswith(u"Masc") and short_features.endswith(u"Sg"):
                output = "Jeder %s ist auch nur ein %s." % (longword, shortword)
            elif long_features.startswith(u"Fem") and short_features.startswith(u"Fem") and short_features.endswith(u"Sg"):
                output = "Jede %s ist auch nur eine %s." % (longword, shortword)
            elif long_features.startswith(u"Neut") and short_features.startswith(u"Neut") and short_features.endswith(u"Sg"):
                output = "Jedes %s ist auch nur ein %s." % (longword, shortword) 
                
        # lower priority output patterns         
        else:              
            if short_pos == u"NN":
                choice = random.randint(1,4)
                if choice > 2:
                    if long_features in noun_patterns:
                        # select random sentence pattern from above
                        output = noun_patterns[long_features][random.randint(0,len(noun_patterns[long_features])-1)] % (longword, shortword)
                else:
                    # this if statement needs to be fixed
                    if short_features.endswith("_Sg") and short_features.split("_", 1)[0] == long_features.split("_", 1)[0] and short_features.split("_",2)[1] == "Nom":
                        output = rev_noun_patterns[long_features][random.randint(0,len(rev_noun_patterns[long_features])-1)] % (shortword, longword)
                                             
            elif short_pos == u"ADJ":
                if long_features in adj_patterns:
                    if short_features.endswith("Invar") or short_features == "Pos_Pred" or short_features == "Pos_Adv" or long_features.split("_",1)[0]+"_Nom" in short_features:
                        output = adj_patterns[long_features][random.randint(0,len(adj_patterns[long_features])-1)] % (longword, shortword) 
            elif short_pos == u"V":   
                if (long_features.endswith("_Pl") and short_features == "3_Pl_Pres_Ind") or (long_features.endswith("_Sg") and short_features == "3_Sg_Pres_Ind"):         
                    output = verb_patterns[long_features][random.randint(0,len(verb_patterns[long_features])-1)] % (longword, shortword) 
                   
        if output != u"Was wäre ein Bot ohne Fehler?":
            print(output)
            api.update_status(output)
            
            # mark combination as already posted
            update = 'UPDATE substring set posted=1 where WortID = %d and SubstringID = %d' % (longID, shortID)
            success = c.execute(update)
            if success:
                conn.commit()
                
            tweeted = True
        
            

post("parsextoto.sqlite")