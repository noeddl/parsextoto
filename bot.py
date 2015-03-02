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


def errorAlert(api, info):
    api.send_direct_message(screen_name = "ojahnn", text = info + " " + time.strftime("%H:%M:%S"))
    return



def getInfoFromDB(longID, shortID, c, c1, c2):
    get_longword = 'select * from Wort where WortID = %d' % (longID)
    longword = c1.execute(get_longword).fetchone()[1]
    get_shortword = 'select * from Wort where WortID = %d' % (shortID)
    shortword = c2.execute(get_shortword).fetchone()[1]

    # retrieving morphological info for each word
    long_query = 'select features from Morph where WortID = %d' % (longID)
    long_features = c.execute(long_query).fetchone()[0]
    short_query = 'select features from Morph where WortID = %d' % (shortID)
    short_features = c.execute(short_query).fetchone()[0]

    return(longword, shortword, long_features, short_features)

def makeNNSentence(longword, shortword, long_features, short_features):
    sentence = ""

    # defining sentences, according to morphological info of longer word
    noun_patterns = {u"Masc_Nom_Sg":["Kein %s ohne %s!", "Kein %s ohne %s."],
                     u"Fem_Nom_Sg":["Undenkbar: Eine %s ohne %s!", u"Was wäre eine %s ohne %s?"],
                     u"Neut_Nom_Sg":["Es gibt kein %s ohne %s.", "Kein %s ohne %s!", "Kein %s ohne %s..."],
                     u"Masc_Nom_Pl": ["Alle %s enthalten %s."],
                     u"Fem_Nom_Pl": ["Alle %s enthalten %s."],
                     u"Neut_Nom_Pl": ["Alle %s enthalten %s."]}

    # TODO: better rev_noun_patterns for plural

    rev_noun_patterns = {u"Masc_Nom_Sg":["Wie kommt der %s in den %s?"],
                         u"Neut_Nom_Sg":["Wie kommt das %s ins %s?"],
                         u"Fem_Nom_Sg":["Wie kommt die %s in die %s?"],
                         u"Masc_Nom_Pl":["Was macht der %s in den %s?"],
                         u"Neut_Nom_Pl":["Was macht das %s in den %s?"],
                         u"Fem_Nom_Pl":["Was macht die %s in den %s?"],
                         }

    # high priority output pattern
    if longword.lower().endswith(shortword.lower()):
        if long_features.startswith(u"Masc") and short_features.startswith(u"Masc") and short_features.endswith(u"Sg"):
            sentence = "Jeder %s ist auch nur ein %s." % (longword, shortword)
        elif long_features.startswith(u"Fem") and short_features.startswith(u"Fem") and short_features.endswith(u"Sg"):
            sentence = "Jede %s ist auch nur eine %s." % (longword, shortword)
        elif long_features.startswith(u"Neut") and short_features.startswith(u"Neut") and short_features.endswith(u"Sg"):
            sentence = "Jedes %s ist auch nur ein %s." % (longword, shortword)

    # lower priority output patterns
    else:
        choice = random.randint(1,4)
        if choice > 2:
            if long_features in noun_patterns:
                # select random sentence pattern from above
                sentence = noun_patterns[long_features][random.randint(0,len(noun_patterns[long_features])-1)] % (longword, shortword)
        else:
            # this if statement needs to be fixed
            if short_features.endswith("_Sg") and short_features.split("_", 1)[0] == long_features.split("_", 1)[0] and short_features.split("_",2)[1] == "Nom":
                sentence = rev_noun_patterns[long_features][random.randint(0,len(rev_noun_patterns[long_features])-1)] % (shortword, longword)

    return sentence

def makeADJSentence(longword, shortword, long_features, short_features):
    sentence = ""

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

    if long_features in adj_patterns:
            if short_features.endswith("Invar") or short_features == "Pos_Pred" or short_features == "Pos_Adv" or long_features.split("_",1)[0]+"_Nom" in short_features:
                sentence = adj_patterns[long_features][random.randint(0,len(adj_patterns[long_features])-1)] % (longword, shortword)

    return sentence

def makeVSentence(longword, shortword, long_features, short_features):
    # reverse sentences to make more interesting
    verb_patterns = {u"Masc_Nom_Sg":["Jeder %s %s."],
                     u"Fem_Nom_Sg":["Jede %s %s."],
                     u"Neut_Nom_Sg":["Jedes %s %s."],
                     u"Fem_Nom_Pl":["Alle %s %s."],
                     u"Masc_Nom_Pl":["Alle %s %s."],
                     u"Neut_Nom_Pl":["Alle %s %s."]}
                     # u"Masc_Dat_Pl":["Das wichtigste am %s ist das %s."]}    # something wrong with this sentence
    if (long_features.endswith("_Pl") and short_features == "3_Pl_Pres_Ind") or (long_features.endswith("_Sg") and short_features == "3_Sg_Pres_Ind"):
        sentence = verb_patterns[long_features][random.randint(0,len(verb_patterns[long_features])-1)] % (longword, shortword)

    return sentence

def post(path, debug = False):
    
    api = login()
    
    # establishing connection to database that contains our vocabulary etc.
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c1 = conn.cursor()
    c2 = conn.cursor()
    

    #while True:            # if you want to tweet without pauses (floods timeline!)
    
    tweeted = False         # set tweeted to an integer if you want to tweet e.g. 3x in a row
    while not tweeted:      
        
        # retrieving word pairs if we want to choose any random pair of words:
        # row = c.execute("select * from Substring where posted = 0 order by random() limit 1").fetchone()

        # decide what kind of POS pair we want to tweet - 1 in 9 will be NN-NN, 4 in 9 will be NN-ADJ, 4 in 9 will be NN-V
        posChoice = random.randint(0, 8)

        output = ""        # default output

        if posChoice == 0:              # NN-NN choice
            row = c.execute('select * from Substring where SubstringID in (select WortID from Wort where POS = "NN") and Score >= 0 and posted = 0 order by random() limit 1').fetchone()       # only pairs of NN + NN
            # note: good NN-NN pairs are scarce, so there is no required Score here as in the other cases
            if row == None:
                errorAlert(api, u"Keine NN-NN-Paare mit den erforderlichen Score- und Posted-Werten mehr übrig! :(")
            else:
                longID = row[0]
                shortID = row[1]
                (longword, shortword, long_features, short_features) = getInfoFromDB(longID, shortID, c, c1, c2)
                output = makeNNSentence(longword, shortword, long_features, short_features)

        elif 1 <= posChoice <= 4:        # NN-ADJ choice
            row = c.execute('select * from Substring where SubstringID in (select WortID from Wort where POS = "ADJ") and Score >= 0.5 and posted = 0 order by random() limit 1').fetchone()       # only pairs of NN + ADJ
            if row == None:
                errorAlert(api, u"Keine NN-ADJ-Paare mit den erforderlichen Score- und Posted-Werten mehr übrig! :(")
            else:
                longID = row[0]
                shortID = row[1]
                (longword, shortword, long_features, short_features) = getInfoFromDB(longID, shortID, c, c1, c2)
                output = makeADJSentence(longword, shortword, long_features, short_features)

        else:                           # NN-V choice
            row = c.execute('select * from Substring where SubstringID in (select WortID from Wort where POS = "V") and Score >= 0.5 and posted = 0 order by random() limit 1').fetchone()       # only pairs of NN + verb
            if row == None:
                errorAlert(api, u"Keine NN-V-Paare mit den erforderlichen Score- und Posted-Werten mehr übrig! :(")
            else:
                longID = row[0]
                shortID = row[1]
                (longword, shortword, long_features, short_features) = getInfoFromDB(longID, shortID, c, c1, c2)
                output = makeADJSentence(longword, shortword, long_features, short_features)


        """
        TODO:
        
        - alle möglichen Features für jedes Wort holen, damit alles vielseitiger wird (Behandlung des Genitivs, weitere
          bisher nicht beachtete Features)
		    - Was bedeutet das Feature Masc_Dat_Sg_OLD?
		    
	    - die Kasus- und Genusprobleme lösen, die zB hier auftreten:
	      https://twitter.com/parsextoto/status/562604744649490432
	      https://twitter.com/parsextoto/status/562958850224312321


	      - KeyError behandeln/vermeiden
		    
        """

        if output != "":
            print(output)
            if not debug:
                api.update_status(output)

                # mark combination as already posted
                update = 'UPDATE Substring set posted=1 where WortID = %d and SubstringID = %d' % (longID, shortID)
                success = c.execute(update)
                if success:
                    conn.commit()

            tweeted = True
        
            

post("parsextoto.sqlite")