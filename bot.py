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
    # enable name-based access to columns
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c1 = conn.cursor()
    c2 = conn.cursor()
    

    while True:            # if you want to tweet without pauses (floods timeline!)
    
    #tweeted = False         # set tweeted to an integer if you want to tweet e.g. 3x in a row
    #while not tweeted:      

        # retrieving word pairs
        # cmd = """
        #     SELECT W1.WortID as totoID, W2.WortID as parsID,
        #            W1.Wort as toto, W2.Wort as pars
        #     FROM Substring as S join Wort as W1 on(S.WortID = W1.WortID) join Wort as W2 on(S.SubstringID = W2.WortID)
        #     WHERE posted = 0 order by random() limit 1
        # """

        cmd = """
            SELECT W1.WortID as totoID, W2.WortID as parsID,
                   W1.Wort as toto, W2.Wort as pars
            FROM Substring as S join Wort as W1 on(S.WortID = W1.WortID) join Wort as W2 on(S.SubstringID = W2.WortID)
            order by random() limit 1
        """

        row = c.execute(cmd).fetchone()

        toto = row['toto']
        pars = row['pars']
        #print toto, pars

        # Get all possible morphological analyses for toto and pars.
        totoFeatList = c.execute("SELECT FeatureID FROM Morph WHERE WortID = %s" % row['totoID']).fetchall()
        parsFeatList = c.execute("SELECT FeatureID FROM Morph WHERE WortID = %s" % row['parsID']).fetchall()

        # Construct query using found analyses and some Python magic.
        totoFeatStr = " or ".join(map(lambda x: 'F1.FeatureID = %s' % x,  [x[0] for x in totoFeatList]))
        parsFeatStr = " or ".join(map(lambda x: 'F2.FeatureID = %s' % x,  [x[0] for x in parsFeatList]))

        if totoFeatStr and parsFeatStr:
            # Enter TemplateID to test one specific template.
            templateID = None
            test = ''
            if templateID:
                test = "and TemplateID = " + str(templateID)

            cmd = """
                SELECT TemplateID, Template, TotoPattern, ParsPattern, SameGender, Suffix,
                       F1.Features as TotoFeatures, F2.Features as ParsFeatures,
                       F1.DeterminerID as TotoDetID, F2.DeterminerID as ParsDetID 
                FROM Template as T
                        join FeaturePattern as FP1 on (T.TotoPattern = FP1.PatternName) join Features as F1 on (FP1.FeatureID = F1.FeatureID)
                        join FeaturePattern as FP2 on (T.ParsPattern = FP2.PatternName) join Features as F2 on (FP2.FeatureID = F2.FeatureID)
                WHERE (%s) and (%s) %s ORDER BY random() limit 1
            """ % (totoFeatStr, parsFeatStr, test)

            sen_row = c.execute(cmd).fetchone()

            if sen_row:
                #print sen_row.keys()
                #print sen_row

                if sen_row['SameGender'] and not same_gender(sen_row['TotoFeatures'], sen_row['ParsFeatures']):
                    continue

                if sen_row['Suffix'] and not toto.endswith(pars.lower()):
                    continue

                sentence = sen_row['Template']

                totoDetID = sen_row['TotoDetID']
                parsDetID = sen_row['ParsDetID']

                if totoDetID and parsDetID:
                    # Get the right determiner row for toto and pars
                    det_toto = c.execute('SELECT * FROM Determiner WHERE DeterminerID=%s' % totoDetID).fetchone()
                    det_pars = c.execute('SELECT * FROM Determiner WHERE DeterminerID=%s' % parsDetID).fetchone()

                    toto = Word(row['toto'], det_toto)
                    pars = Word(row['pars'], det_pars)

                    s = sentence.format(toto=toto, pars=pars)
                    s = end(s)
                    output = s[0].capitalize() + s[1:]

                    print(output)
                    #api.update_status(output)
                    
                    # mark combination as already posted
                    #update = 'UPDATE substring set posted=1 where WortID = %d and SubstringID = %d' % (row['totoID'], row['parsID'])
                    #success = c.execute(update)
                    #if success:
                    #    conn.commit()
                        
                tweeted = True

def same_gender(totoFeat, parsFeat):
    for gen in ['Neut', 'Masc', 'Fem']:
        if gen in totoFeat and gen in parsFeat:
            return True
    return False
        
class Word():

    def __init__(self, s, det_row):
        self.self = s
        self.das = None
        self.ein = None
        self.jedes = None
        self.kein = None
        self.welches = None
        if det_row:
            self.das = det_row['das']
            self.ein = det_row['ein']
            self.jedes = det_row['jedes']
            self.kein = det_row['kein']
            self.welches = det_row['welches']

def end(s):
    if not s[-1] in ['.', '!', '?']:
        return s + random.choice(['.', '!'])
    return s            

post("parsextoto.sqlite")
#test("parsextoto.sqlite")

