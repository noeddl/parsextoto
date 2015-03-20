#!/usr/bin/python
# -*- coding: utf-8 -*-

import random
import sqlite3

# establishing connection to database that contains our vocabulary etc.
conn = sqlite3.connect("parsextoto.sqlite")
# enable name-based access to columns
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS Template")
cmd = """
	CREATE TABLE Template (
		TemplateID INTEGER PRIMARY KEY AUTOINCREMENT,
		Template TEXT,
		TotoPattern TEXT,
		ParsPattern TEXT,
		Suffix BOOLEAN,
		SameGender BOOLEAN
	)
"""
c.execute(cmd)

sen_tmp = [
	(u'{toto.kein} {toto.self} ohne {pars.self}', 'NN:Nom_Sg', 'NN:Nom', 0, 0),
	(u'{toto.jedes} {toto.self} ist {pars.self}', 'NN:Nom_Sg', 'ADJ:Pos_Pred', 0, 0),
	(u'{toto.jedes} {toto.self} {pars.self}', 'NN:Nom_Sg', 'V:3_Sg_Pres_Ind', 0, 0),
	(u'{toto.jedes} {toto.self} ist {pars.ein} {pars.self}', 'NN:Nom_Sg', 'ADJ:Pos_Nom_Sg_St', 0, 1),
	(u'{toto.jedes} {toto.self} ist auch nur {pars.ein} {pars.self}', 'NN:Nom_Sg', 'NN:Nom_Sg', 1, 0),
	(u'Zu {toto.jedes} {toto.self} gehört {pars.ein} {pars.self}', 'NN:Dat_Sg', 'NN:Nom_Sg', 0, 0),
	(u'In {toto.jedes} {toto.self} steckt {pars.ein} {pars.self}', 'NN:Dat_Sg', 'NN:Nom_Sg', 0, 0),
	(u'{pars.das} {pars.self} ist Teil {toto.jedes} {toto.self}', 'NN:Gen_Sg', 'NN:Nom_Sg', 0, 0),
	(u'{toto.welches} {toto.self} ist {pars.das} {pars.self}?', 'NN:Nom_Sg', 'ADJ:Sup_Nom_Sg_St', 0, 1),
]

c.executemany('INSERT INTO Template VALUES (NULL, ?, ?, ?, ?, ?)', sen_tmp)

c.execute("DROP TABLE IF EXISTS Determiner")
cmd = """
	CREATE TABLE Determiner (
		DeterminerID INTEGER PRIMARY KEY AUTOINCREMENT,
		das TEXT, ein TEXT, jedes TEXT, kein TEXT, welches TEXT
	)
"""
c.execute(cmd)

c.execute("DROP TABLE IF EXISTS FeaturePattern")

cmd = "CREATE TABLE FeaturePattern (PatternName TEXT, FeatureID INTEGER)"

c.execute(cmd)

# NN:Neut_Nom_Sg_St : ein makes no sense (better: etwas)

values = [
	('das', 'ein',   'jedes', 'kein',	'welches'),	# 1
	('der', 'ein',   'jeder', 'kein',	'welcher'),	# 2
	('die', 'eine',  'jede',  'keine',	'welche'),	# 3
	('das',  None,   'jedes',  None,	'welches'),	# 4
	('der',  None,   'jeder',  None,	'welcher'),	# 5
	( None, 'ein',    None,   'kein',	 None),	# 6
	('den', 'einen', 'jeden', 'keinen',	'welchen'), # 7
	('dem', 'einem', 'jedem', 'keinem',	'welchem'), # 8
	('des', 'eines', 'jedes', 'keines',	'welches'), # 9
	('der', 'einer', 'jeder', 'keiner',	'welcher'), # 10
	('die',  None,    None,   'keine',	'welche'),  # 11
	('den',  None,    None,   'keinen',	'welche'), # 12
	('der',  None,    None,   'keiner',	'welchen'), # 13
	('',    '',      '',      '',		'')			# 14
]

c.executemany('INSERT INTO Determiner VALUES (NULL, ?, ?, ?, ?, ?)', values)

# Map feature combinations to the corresponding determiner pattern id.
feats2det = {}

def add_adj_det(gen, cas, num, decl, detID):
	# NN inflected like ADJ
	feats2det["NN:{}_{}_{}_{}".format(gen, cas, num, decl)] = detID
	# ADJ: Use the same determiner for all comparison modes.
	for comp in ['Pos', 'Comp', 'Sup']:
		feats2det["ADJ:{}_{}_{}_{}_{}".format(comp, gen, cas, num, decl)] = detID

def add_det(gen, cas, num, detID, detID_Wk, detID_St):
	if not gen:
		for gen in ['Neut', 'Masc', 'Fem']:
			add_det(gen, cas, num, detID, detID_Wk, detID_St)
	else:
		# regular NN
		feats2det["NN:{}_{}_{}".format(gen, cas, num)] = detID
		if cas == 'Dat':
			# "Old" dative (dem Haus vs. dem Hause).
			feats2det["NN:{}_{}_{}_Old".format(gen, cas, num)] = detID # to do: correct wrong version in DB
		# ADJ / ADJ-NN
		add_adj_det(gen, cas, num, 'Wk', detID_Wk)
		add_adj_det(gen, cas, num, 'St', detID_St)

# TO DO: NoGend

# Neut						# NN Wk St
add_det('Neut', 'Nom', 'Sg',  1, 4, 6)
add_det('Neut', 'Acc', 'Sg',  1, 4, 6)
add_det('Neut', 'Dat', 'Sg',  8, 8, 14)
add_det('Neut', 'Gen', 'Sg',  9, 9, 14)

# Masc
add_det('Masc', 'Nom', 'Sg',  2, 5, 6)
add_det('Masc', 'Acc', 'Sg',  7, 7, 14)
add_det('Masc', 'Dat', 'Sg',  8, 8, 14)
add_det('Masc', 'Gen', 'Sg',  9, 9, 14 )

# Fem
add_det('Fem',  'Nom', 'Sg',  3, 3, 3)
add_det('Fem',  'Acc', 'Sg',  3, 3, 3)
add_det('Fem',  'Dat', 'Sg',  10, 10, 10)
add_det('Fem',  'Gen', 'Sg',  10, 10, 10)

# Pl
add_det( None,  'Nom', 'Pl',  11, 11, 14)
add_det( None,  'Acc', 'Pl',  11, 11, 14)
add_det( None,  'Dat', 'Pl',  12, 12, 14)
add_det( None,  'Gen', 'Pl',  13, 13, 14)

for k in sorted(feats2det):
	#print k, feats2det[k]
	c.execute('UPDATE Features SET DeterminerID = ? WHERE Features = ?', (feats2det[k], k))


feat_ids = {}

cases = ['Nom', 'Acc', 'Dat', 'Gen']
genders = ['Neut', 'Masc', 'Fem'] # NoGend?
numbers = ['Sg', 'Pl']
ndecl = [None, 'Wk', 'St'] # noun declencion
adecl = ['Wk', 'St'] # adj declension
comps = ['Pos', 'Comp', 'Sup']


# to do: template? feature pattern?
# def build_template(wordclass, cas, num):
# 	name = "{}:{}_{}".format(wordclass, cas, num)
# 	for (gen, decl) in ((gen, decl) for gen in genders for decl in ndecl):
# 		tmp = "{}:{}_{}_{}".format(wordclass, gen, cas, num)
# 		if decl:
# 			tmp = "{}:{}_{}_{}_{}".format(wordclass, gen, cas, num, decl)
# 		yield name, tmp

def build_template(pos, *arg):
	# Build list with all function arguments that are not None.
	l = [e for e in arg if e]
	# Construct string such as NN:Neut_Nom_Sg
	return '{}:{}'.format(pos, '_'.join(l))

cmd = """
	INSERT INTO FeaturePattern
	VALUES (?, (SELECT FeatureID FROM Features WHERE Features = ?))
"""

# Nouns
for (cas, num) in ((cas, num) for cas in cases for num in numbers):
	uber = build_template('NN', cas)
	name = build_template('NN', cas, num)
	for (gen, decl) in ((gen, decl) for gen in genders for decl in ndecl):
		feats = build_template('NN', gen, cas, num, decl)
		c.executemany(cmd, [(uber, feats), (name, feats)])

# ADJ - predicative
for comp in comps:
	pred = build_template('ADJ', comp, 'Pred')
	invar = build_template('ADJ', comp, 'Invar')
	c.executemany(cmd, [(pred, pred), (pred, invar)])

# ADJ - attributive
# Pos_(Masc)_Nom_Sg_St
for (comp, cas, num, decl) in ((comp, cas, num, decl) for comp in comps for cas in cases for num in numbers for decl in adecl):
	name = build_template('ADJ', comp, cas, num, decl)
	for gen in genders:
		feat = build_template('ADJ', comp, gen, cas, num, decl)
		c.execute(cmd, (name, feat))

# There's not much verb stuff going on for now, so here's just a hack.
c.executemany(cmd, [('V:3_Pl_Past_Ind', 'V:3_Pl_Past_Ind'),
	                ('V:3_Pl_Pres_Ind', 'V:3_Pl_Pres_Ind'),
	                ('V:3_Sg_Pres_Ind', 'V:3_Sg_Pres_Ind'),
	                ('V:3_Sg_Past_Ind', 'V:3_Sg_Past_Ind'),
	               ])

# empty determiner? (Kein X ohne Y - kann Y alles sein?)

# Clean rows where FeatureID is NULL.
c.execute('DELETE FROM FeaturePattern WHERE FeatureID is NULL')

conn.commit()

conn.close()

# SELECT Wort, Features, das, ein, jedes, kein FROM Wort join Morph using(WortID) join Features using(FeatureID) join Determiner using(DeterminerID) WHERE Wort like "Hund%"

# Features = "ADJ:Pos_Neut_Dat_Sg_St"

