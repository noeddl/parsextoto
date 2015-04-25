#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

# Some prefixes and suffixes that make a pars less interesting.
#PREFIXES = ['ab', 'an', 'auf']
#SUFFIXES = ['ant', 'atisier', 'atik', 'e', 'ei', 'en', 'er', 'es', 'heit', 'iat', 'ien', 'ier', 'ig', 'igkeit', 'ik', 'inne', 'innen', 'isier', 'ium', 'keit', 'ler', 'n', 'nen', 'ner', 'r', 'rer', 's', 'ten', 'ung', 'ur']
PREFIXES = [
	'an',	# Krank#en#geld#anspruch, Spruch
	'be',	# Hof#bedienstet#e, Dienste
	'ein',	# Einsatz#gewicht, Satz#gewicht
	'ent',	# Entlade#frist, Lade#frist
	'er',	# Not#rad#erkenn#ung, Kennung
	'ge',	# Geschraub#t#heit, schraub#t
	'un',	# Unbedingt#heit, bedingt
	'ver',	# Verbind#ungs#zeichen#folge, Bindungs#zeichen
	]
SUFFIXES = [
	'age',		# Spionage#ab#wehr#einheit, Spion
	'atik',		# Einsatz#systematik, Satzsystem
	'en',		# Satelliten#sendung, Satellit
	'es',		# Gesetzes#vorschrift, Gesetz
	'heit',		# Berg#gottheit, Berggott
	'ie',		# Hoch#frequenz#astronomie, Astronom
	'ien',		# Berechn#ungs#prinzipien, Berechn#ungs#prinzip
	'ig',		# gesetzes#artig, Gesetzes#art
	'in',		# Akte#urin, Akteur
	'inne',		# Ferien#dorf#bet#reibe#rinne#n, Ferien#dorf#betreib#er
	'ion',		# Daten#korrelation, Korrelat
	'ions',		# Argumentations#figur, Argument
	'ium',		# Raum#ordnungs#ministerium, Raum#ordnungs#minister
	'isations', # Organisations#disziplin, Organ
	'isier',	# Inventarisier#ungs#technik, Inventar
	'n',		# Kassen#anzeige, Kasse
	'nde',		# Polar#reisende, Polar#reis#e
	'nis',		# Gesam#t#bildnis, Gesam#t#bild
	'onisch',	# landschafts#architektonisch, Landschafts#architekt
	'rie',		# Antriebs#maschinerie, Antriebs#maschine
	's',		# Alpen#vereins#sektion, Alpen#verein
	'schafts',	# Berg#wirtschafts#lehre, Bergwirt
	'ung',		# Her#stell#ungs#abteilung, Abteil
	'ur',		# Gewebe#architektur, Architekt
	'ut',		# Energie#armut, energie#arm
]

# Haus#angestellte, angestellt
# Drei#achs#er, Achse
# Keine Indoktrinierung ohne Doktrin!

# TO DO: don't print None
class Word():

    def __init__(self, s, id, morph):
        self.self = s
        self.id = id
        self.morph = morph
        self.bounds = self.set_bounds()
        self.feats = None
        self.prefix = ''
        self.suffix = ''
        self.score = 0
        # Determiners.
        self.das = None
        self.ein = None
        self.jedes = None
        self.kein = None
        self.welches = None

    def __len__(self):
    	return len(self.self)

    def __str__(self):
    	return self.self

    def set_bounds(self):
    	bounds = [0]
    	for m in self.morph.split('#'):
    		bounds.append(bounds[-1] + len(m))
    	return bounds

	# Get all possible morphological analyses and construct WHERE clause using found analyses and some Python magic.
	# Don't try to join these huge Morph tables with each other and all the rest. Seriously. Just don't.
    def set_feats(self, conn, feat_id):
    	iter = conn.execute("SELECT FeatureID FROM Morph WHERE WortID = %s" % self.id).fetchall()
    	self.feats = " OR ".join(map(lambda x: 'F{}.FeatureID = {}'.format(feat_id, x),  (x['FeatureID'] for x in iter)))

    def set_dets(self, conn, det_id):
    	det_row = conn.execute('SELECT * FROM Determiner WHERE DeterminerID = ?', (det_id,)).fetchone()

    	self.das = det_row['das']
    	self.ein = det_row['ein']
    	self.jedes = det_row['jedes']
    	self.kein = det_row['kein']
    	self.welches = det_row['welches']

class WordPair():

	words = {}

	def __init__(self, toto, pars, offset):
		self.toto = toto
		self.pars = pars
		self.offleft = offset - 1 # offset in SQL function instr starts at 1 (0 means no offset).
		self.offright = self.offleft + len(self.pars) # TO DO: Rename this variable.
		self.score = 0

	# Compute number of morphemes in toto that are overlapped by pars and get prefix and suffix of pars.
	def get_morph_score(self):
		i_start = None
		i_end = None

		for i in range(len(self.toto.bounds)):
			b_index = self.toto.bounds[i]
			if self.offright <= b_index:			
				self.pars.suffix = self.toto.self[self.offright:b_index]
				i_end = i
				break

		for i in range(len(self.toto.bounds)-1, -1, -1):
			b_index = self.toto.bounds[i]
			if self.offleft >= b_index:
				self.pars.prefix = self.toto.self[b_index:self.offleft]
				i_start = i
				break

		morph_score = (i_end - i_start)
		return morph_score

	def get_affix_score(self, affix, affixes):
		affix = affix.lower()
		# If pars is preced/followed by a common (derivation) affix, it's probably boring.
		if affix in affixes:
			return 0.1
		
		# If the rest string till the next/previous boundary is a word itself, it's probably boring.
		if (WordPair.words.get(affix)):
			return 0.1

		# If pars is aligned with one of totos morpheme boundaries, it's proabably boring.
		if not affix:
			return 0.1

		return 1

	def get_phon_score(self):
		# Match sounds that are made up by several letters.
		re_phon = re.compile(u'tsch|sch|tio|ch|ck|pf|sp|st|ng|nk|tz|th|dt|qu|ieu|ei|ai|au|ea|eu|äu|oi|ie|aa|oo|ou|ee|[a-zßäöü]')

		phon_pos = [p.start() for p in re_phon.finditer(self.toto.self.lower())]

		phon_score = 1

		if not self.offleft in phon_pos:
			phon_score += 0.1

		if not self.offright in phon_pos:
			phon_score += 0.1

		return phon_score

	def compute_score(self):
		score = 0

		# Words with only 2 letters are really uncool.
		if len(self.pars) < 3:
			return 0

		# Longer words are prefered over shorter words.
		len_score = float(len(self.pars))/float(len(self.toto))
		
		# The more toto morphemes are involved, the better.
		morph_score = self.get_morph_score()

		# Make sure that the surroundings of pars in toto are interesting.
		prefix_score = self.get_affix_score(self.pars.prefix, PREFIXES)
		suffix_score = self.get_affix_score(self.pars.suffix, SUFFIXES)
		affix_score = prefix_score * suffix_score

		# # It's more interesting if pars is not directly at the start or end of toto.
		# position_score = self.get_position_score(pars)
		
		# Assign extra points if "phoneme boundaries" are crossed.
		phon_score = self.get_phon_score()

		# # The world formula!
		score = (len_score * morph_score * affix_score * phon_score)

		return score

	def set_feats(self, conn):
		self.toto.set_feats(conn, 1)
		self.pars.set_feats(conn, 2)

	def set_dets(self, conn, totoDetID, parsDetId):
		if totoDetID:
			self.toto.set_dets(conn, totoDetID)
		if parsDetId:
			self.pars.set_dets(conn, parsDetId)

