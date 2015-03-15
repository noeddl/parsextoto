#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sqlite3

connection = sqlite3.connect("parsextoto.sqlite")
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

#cursor.execute("DROP TABLE IF EXISTS Substring")
#cursor.execute('CREATE TABLE Substring (WortID INTEGER, SubstringID INTEGER, Score FLOAT, posted BOOL)')

# Some prefixes and suffixes that make a pars less interesting.
PREFIXES = ['ab', 'an', 'auf']
SUFFIXES = ['ant', 'atisier', 'atik', 'e', 'ei', 'en', 'er', 'es', 'heit', 'iat', 'ien', 'ier', 'ig', 'igkeit', 'ik', 'inne', 'innen', 'isier', 'ium', 'keit', 'ler', 'n', 'nen', 'ner', 'r', 'rer', 's', 'ten', 'ung', 'ur']

class Word():

	def __init__(self, row):
		self.id = row['WortID']
		self.word = row['Wort']
		self.pos = row['POS']
		self.morph = row['Morpheme']
		self.boundaries = self.get_morph_boundaries(self.morph)
		# Start and end in relation to a potential toto.
		self.start = 0
		self.end = len(self.word)
		# Prefix and suffix until the next morpheme boundary in toto.
		self.prefix = ''
		self.suffix = ''

	def get_morph_boundaries(self, morph):
		boundaries = [0]
		for m in morph.split('#'):
			boundaries.append(boundaries[-1] + len(m))
		return boundaries

	# Compute number of morphemes in toto that are overlapped by pars and get prefix and suffix of pars.
	def get_morph_score(self, pars):
		i_start = None
		i_end = None

		for i in range(len(self.boundaries)):
			b_index = self.boundaries[i]
			if pars.end <= b_index:			
				pars.suffix = self.word[pars.end:b_index]
				i_end = i
				break

		for i in range(len(self.boundaries)-1, -1, -1):
			b_index = self.boundaries[i]
			if pars.start >= b_index:
				pars.prefix = self.word[b_index:pars.start]
				i_start = i
				break

		morph_score = (i_end - i_start)
		return morph_score

	def get_affix_score(self, affix, affixes):
		# If pars is preced/followed by a common (derivation) affix, it's probably boring.
		if affix in affixes:
			return 0.1
		
		# If the rest string till the next/previous boundary is a word itself, it's probably boring.
		if (pars_dict.get(affix) or pars_dict.get(affix.capitalize())):
			return 0.1
		# Doing the same with affix.lower() downvotes e.g. Abendlicht - endlich.

		# If pars is aligned with one of totos morpheme boundaries, it's proabably boring.
		if not affix:
			return 0.1

		return 1

	def get_position_score(self, pars):
		if pars.start == 0 or pars.end == self.end:
			return 0.5

		return 1

	def get_phon_score(self, pars):
		# Match sounds that are made up by several letters.
		re_phon = re.compile(u'tsch|sch|tio|ch|ck|pf|sp|st|ng|nk|tz|th|dt|qu|ieu|ei|ai|au|ea|eu|äu|oi|ie|aa|oo|ou|ee|[a-zßäöü]')

		phon_pos = [p.start() for p in re_phon.finditer(self.word.lower())]

		phon_score = 1

		if not pars.start in phon_pos:
			phon_score += 0.1

		if not pars.end in phon_pos:
			phon_score += 0.1

		return phon_score

	def compute_score(self, pars):
		score = 0

		# Longer words are prefered over shorter words.
		len_score = float(len(pars.word))/float(len(self.word))
		
		# The more toto morphemes are involved, the better.
		morph_score = self.get_morph_score(pars)

		# Make sure that the surroundings of pars in toto are interesting.
		prefix_score = self.get_affix_score(pars.prefix, PREFIXES)
		suffix_score = self.get_affix_score(pars.suffix, SUFFIXES)
		affix_score = prefix_score * suffix_score

		# It's more interesting if pars is not directly at the start or end of toto.
		position_score = self.get_position_score(pars)
		
		# Assign extra points if "phoneme boundaries" are crossed.
		phon_score = self.get_phon_score(pars)

		# The world formula!
		score = (len_score * morph_score * affix_score * position_score * phon_score)

		return score

	def find_parse(self):
		# Loop over substrings of toto.
		for i in range(len(self.word)):
			# pars has has to be at least 3 characters long.
			for j in range(i+3, len(self.word)+1):
				# Ignore pars if it is equal to toto.
				if i > 0 or j < len(self.word):
					w = self.word[i:j]
					pars = pars_dict.get(w) or pars_dict.get(w.capitalize()) or pars_dict.get(w.lower())
					if pars:
						pars.start = i
						pars.end = j
						score = self.compute_score(pars)
						if score > 0.15:
							yield pars, score

toto_list = []
pars_dict = {}

# Collect all the words from the database.
for row in cursor.execute('SELECT * FROM Wort'):
	w = Word(row)

	pars_dict[w.word] = w

	# Only nouns can be toto.
	if w.pos == 'NN':
		toto_list.append(w)

pairs = {}

for row in cursor.execute('SELECT * FROM Substring'):
	k = "%s_%s" % (row['WortID'], row['SubstringID'])
	pairs[k] = True

# Find pars for toto!
for toto in toto_list:
	for pars, score in toto.find_parse():
		# Insert only if the entry does not exist yet.
		if not pairs.get("%s_%s" % (toto.id, pars.id)):
			#print "%s\t%s\t%.2f" % (toto.word, pars.word, score)
			cursor.execute('INSERT INTO Substring (WortID, SubstringID, Score, posted) VALUES (%s, %s, %.2f, 0)' % (toto.id, pars.id, score))	

connection.commit()
