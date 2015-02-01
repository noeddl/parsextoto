#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import codecs
import sqlite3

f = codecs.open('lemma.txt', encoding='utf-8')

analyses = {}
features = {}

word = None

connection = sqlite3.connect("parsextoto.sqlite")
# Enable access to attributes by dictionary keys.
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute("DROP TABLE IF EXISTS Wort")
cursor.execute("DROP TABLE IF EXISTS Morph")

cursor.execute('CREATE TABLE Wort (WortID INTEGER PRIMARY KEY, Wort TEXT, POS TEXT, Morpheme TEXT)')
cursor.execute('CREATE TABLE Morph (WortID INTEGER, Features TEXT)')

word_id = 0
done = True
first_analysis = False
forms = {}

for line in f:
	line = line.strip()
	if line.startswith('>'):
		word = line[2:]
		#print word, word[0:-2], forms.get(word[0:-2])

		# Exclude inflection of extremely long words.
		if len(word) < 10 or (not forms.get(word[0:-1]) and not forms.get(word[0:-2])):
			word_id += 1
			first_analysis = True
			done = False

			if word_id % 10000 == 0:
				print word_id, word
				connection.commit()	
		else:
			done = True
		
		forms[word] = True

	elif not done and not line.startswith('no'):
		#print line

		morph = ''
		tag = None
		feats = []
		boundary = '#'

		# Match
		# 1. token1:token2 - token is either a single letter or something in <>
		# 2. a single letter.
		# This returns a triple of the form (token1, token2, single letter).
		re_trans = re.compile(u'([a-zA-Zäöüß]|<.*?>):([a-zA-Zäöüß]|<.*?>)|([a-zA-Zäöüß])')
		matches = re_trans.findall(line)
		length = 0
		for i, m in enumerate(matches):
			#print m
			token1 = m[0]
			token2 = m[1]
			single = m[2]

			# Single letter matches: simple append it.
			if single:
				morph += single
				length += 1
			elif token1.startswith('<'):
				# Token one is empty: append token2 (e.g. a suffix)
				if token1 == '<>':
					morph += token2
					length += 1
				# Collect morph info.
				else:
					if tag:
						feats.append(token1.replace('<','').replace('>',''))
					else:
						if token1.startswith('<+'):
							tag = token1
						if length < len(word):
							if not (morph.endswith('#')):
								morph += '#'
					# Mapping of features to letters.
					if not token2.startswith('<'):
						morph += token2
			# Mapping of letters to other letters or removal of letters.
			elif token1 and (token2 != '<>'):
				morph += token2
				length += 1

		if tag: #and tag in ['<+NN>', '<+ADJ>'] or (tag == '<+V>' and '3' in feats):
			tag = tag.replace('<','').replace('+', '').replace('>', '')
			ok_noun = (tag == 'NN') #and ('Nom' in feats)
			ok_verb = (tag == 'V') and '3' in feats and 'Ind' in feats
			ok_adj = (tag == 'ADJ')

			if ok_noun or ok_verb or ok_adj:
				if first_analysis:
					#print morph, tag, '_'.join(feats)

					cmd = u'INSERT INTO Wort (WortID, Wort, POS, Morpheme) VALUES (%s, "%s", "%s", "%s")' % (word_id, word, tag, morph)
					cursor.execute(cmd)

					first_analysis = False
				
				cursor.execute(u'INSERT INTO Morph (WortID, Features) VALUES (%s, "%s")' % (word_id, '_'.join(feats)))
	

			
