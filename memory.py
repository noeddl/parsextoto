#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3

COUNT_USED_WORDS = 1000
COUNT_USED_TEMPS = 10

# Use extra database to keep track of used words and sentences templates.
class Memory():

	def __init__(self):
		self.conn = sqlite3.connect("memory.sqlite")
		self.conn.row_factory = sqlite3.Row
		# Create table if it does not exist.
		cmd = """
			CREATE TABLE IF NOT EXISTS Memory (
				TotoID INTEGER,
				ParsID INTEGER,
				TotoPattern TEXT,
				ParsPattern TEXT,
				Sentence TEXT
			)
		"""
		self.conn.execute(cmd)
		
		self.used_words = set()
		self.used_temps = set()

		self.init()
		#print self.used_words
		#print self.used_temps

	def init(self):
		for i, row in enumerate(self.conn.execute('SELECT * FROM Memory ORDER BY rowid DESC').fetchmany(COUNT_USED_WORDS)):
			self.used_words.add(row['TotoID'])
			self.used_words.add(row['ParsID'])
			if i < COUNT_USED_TEMPS:
				key = '{}-{}'.format(row['TotoPattern'], row['ParsPattern'])
				self.used_temps.add(key)

	def is_used_wordpair(self, toto_id, pars_id):
		return toto_id in self.used_words \
			or pars_id in self.used_words

	def is_used_template(self, toto_pattern, pars_pattern):
		k = '{}-{}'.format(toto_pattern, pars_pattern)
		return k in self.used_temps

	def save(self, toto_id, pars_id, toto_pattern, pars_pattern, sentence):
		self.conn.execute('INSERT INTO Memory VALUES (?,?,?,?,?)', (toto_id, pars_id, toto_pattern, pars_pattern, sentence))
		self.conn.commit()

	def close(self):
		self.conn.close()

