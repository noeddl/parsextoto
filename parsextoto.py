#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import random
import sqlite3

from word_pair import Word, WordPair
from memory import Memory

conn = sqlite3.connect("parsextoto.sqlite")
conn.row_factory = sqlite3.Row

# This is the main class that keeps everything together.
class Parsextoto():

	def __init__(self):
		self.memory = Memory()
		self.init_words()
		conn.create_function('same_gender', 3, self.same_gender)
		conn.create_function('suffix', 3, self.suffix)
		conn.create_function('is_used_wordpair', 2, self.memory.is_used_wordpair)
		conn.create_function('is_used_template', 2, self.memory.is_used_template)
		
	def init_words(self):
		for row in conn.execute('SELECT * FROM Wort WHERE Morpheme not like "%#%"'):
			WordPair.words[row['Wort'].lower()] = True	

	def reset(self):
		self.memory = Memory()
		conn.create_function('is_used_wordpair', 2, self.memory.is_used_wordpair)
		conn.create_function('is_used_template', 2, self.memory.is_used_template)

	def get_random_id(self, table):
		row_count = conn.execute('SELECT COUNT(*) FROM {}'.format(table)).fetchone()[0]
		return random.randint(1, row_count)		

	def get_random_words(self, count=10):
		word_ids = set()

		while len(word_ids) < count:
			word_id = self.get_random_id('Wort')
			if not word_id in self.memory.used_words:
				word_ids.add(word_id)

		return word_ids

	def suffix(self, toto, pars, required):
		return toto.endswith(pars.lower()) == required #or required == 0

	def same_gender(self, totoFeat, parsFeat, required):
		if not required:
			return True

		for gen in ['Neut', 'Masc', 'Fem']:
			if gen in totoFeat and gen in parsFeat:
				return True
		return False

	# Get random sentence end marker in case there isn't one already.
	def end(self, s):
		if not s[-1] in ['.', '!', '?']:
			return s + random.choice(['.', '!'])
		return s
			
	def get_word_pair(self):
		word_id = self.get_random_id('Wort')

		#word_ids = self.get_random_words(5)
		#where_id = ' or '.join(map(lambda x: 'W1.WortID = %s' % x, word_ids))

		# Tried to compute score in this query but it seems to be faster to do it as an extra step.
		cmd = """
			SELECT W1.Wort AS Word1, W1.WortID AS Word1ID, W1.Morpheme AS Word1Morph,
		 	       W2.Wort AS Word2, W2.WortID AS Word2ID, W2.Morpheme AS Word2Morph,
		 	       instr(lower(W1.Wort), lower(W2.Wort)) as offset1,
		  		   instr(lower(W2.Wort), lower(W1.Wort)) as offset2
			FROM Wort as W1 join Wort as W2
			WHERE W1.WortID != W2.WortID
			  AND W1.WortID = {}
			  AND (offset1 > 0 OR offset2 > 0)
			  AND NOT is_used_wordpair(Word1ID, Word2ID)
		""".format(word_id) #.format(where_id)
		# AND W1.WortID = {}
		# AND ({})

		pairs = {}

		for row in conn.execute(cmd):
			word1 = Word(row['Word1'], row['Word1ID'], row['Word1Morph'])
			word2 = Word(row['Word2'], row['Word2ID'], row['Word2Morph'])

			wp = WordPair(word1, word2, row['offset1'])

			if row['offset2'] > 0:
				wp = WordPair(word2, word1, row['offset2'])

			score = wp.compute_score()

			#print wp.toto, wp.pars, wp.offleft, wp.offright, score

			if score > 0.15:
				wp.score = score
				pairs[wp] = score

		return pairs

	def iter_word_pairs(self):
		while True:
			pairs = self.get_word_pair()
			for wp in sorted(pairs, key=pairs.get, reverse=True):
				yield wp

	def get_template(self, wp):
		templateID = None
		test = ''
		if templateID:
			test = "and TemplateID = " + str(templateID)

		where = 'AND NOT is_used_template(T.TotoPattern, T.ParsPattern)'
		print wp.score

		# If the wordpair score is exeptionally high, allow all templates.
		if wp.score > 0.6:
			print 'High score!'
			where = ''

		cmd = """
			SELECT TemplateID, Template, TotoPattern, ParsPattern, SameGender, Suffix,
					F1.Features as TotoFeatures, F2.Features as ParsFeatures,
					F1.DeterminerID as TotoDetID, F2.DeterminerID as ParsDetID
			FROM Template as T
					join FeaturePattern as FP1 on (T.TotoPattern = FP1.PatternName) join Features as F1 on (FP1.FeatureID = F1.FeatureID)
					join FeaturePattern as FP2 on (T.ParsPattern = FP2.PatternName) join Features as F2 on (FP2.FeatureID = F2.FeatureID)
			WHERE ({}) and ({})
				AND suffix("{}", "{}", T.Suffix)
				AND same_gender(F1.Features, F2.Features, T.SameGender)
				{}
			ORDER BY random() limit 1
		""".format(wp.toto.feats, wp.pars.feats, wp.toto.self, wp.pars.self, where)
		#ORDER BY random() limit 1
		#AND NOT is_used_template(T.TotoPattern, T.ParsPattern)

		return conn.execute(cmd).fetchone()
		#return conn.execute(cmd)

	def iter_templates(self, wp):
		for row in self.get_template(wp):
			yield row

	def format(self, temp, wp):
		s = temp.format(toto=wp.toto, pars=wp.pars)
		s = self.end(s)

		return s[0].capitalize() + s[1:]

	def get_sentence(self):

		for wp in self.iter_word_pairs():
			wp.set_feats(conn)

			print wp.toto, wp.pars

			sen_row = self.get_template(wp)

			if sen_row:
			#for sen_row in self.iter_templates(wp):
				temp = sen_row['Template']

				wp.set_dets(conn, sen_row['TotoDetID'], sen_row['ParsDetID'])

				sentence = self.format(temp, wp)

				print sen_row['TemplateID'], sen_row['TotoPattern'], sen_row['ParsPattern'], wp.toto.morph, wp.pars.morph

				self.memory.save(wp.toto.id, wp.pars.id, sen_row['TotoPattern'], sen_row['ParsPattern'], sentence)

				return sentence

	def close(self):
		self.memory.close()

