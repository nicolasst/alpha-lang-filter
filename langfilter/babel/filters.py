
from abc import ABC, abstractmethod
import unicodedata

from langfilter.babel.db import scriptdb, languagedb, alphabetdb, unicodedb

class AbstractFilter(ABC):

	def __init__(self, value):
		self.value = value
		super().__init__()

	@abstractmethod
	def decide(self, s):
		pass

class UnicodeFilter(AbstractFilter):

	def __init__(self, script, verbose=False):

		if script == "Hans" or script == "Hant":
			script = "Hani"

		self.script = script
		self.verbose = verbose

		self.searchscript_id = unicodedb.map_iso_idx[self.script]

	def decide(self, word):
		accept = True
		for idx, c in enumerate(word):
			codepoint = ord(c)
			script_id = unicodedb.map_codepoint_idx[codepoint]
			if script_id != self.searchscript_id:

				category = unicodedata.category(c)
				try:
					name = unicodedata.name(c)
				except:
					name = "UNDEFINED"
				if category[0] == 'L':
					if self.verbose:
						print("verbose: character not in script: index", idx, "char", c, "codepoint", codepoint, "unicode range index", script_id, "unicode range name", unicodedb.map_blockidx_blockname[unicodedb.map_codepoint_blockidx[codepoint]] ,"category", category, "name", name, "input:", word)
						return False
#				else:
#					if self.search_configuration.strict_alpha:
#						if self.verbose:
#							print("verbose: reject input:", word)
#							print("verbose: character not a letter or a space: index", idx, "char", c, "codepoint", codepoint, "unicode range index", script_id, "category", category, "name", name, "input:", word)
#						return False
					accept &= False
					break
			else:
				accept &= True

		return accept

	def __call__(self, t):
		return self.decide(t)


class AlphabetFilter(AbstractFilter):

	def __init__(self, lang, script, no_fail=False):

		self.lang = lang
		self.script = script

		if lang not in languagedb:
			raise Exception("Error: unsupported lang: "+lang)
		if script not in scriptdb:
			raise Exception("Error: unsupported script: "+script)

		scriptid = unicodedb.map_iso_idx[script]

		if [lang, script] not in alphabetdb:
			raise Exception("Error: unsupported lang/script pair"+ script)

		self.valid_codepoint = alphabetdb.getCharacters(lang, script)

	def __call__(self, t):
		return self.decide(t)

	def decide(self, word):

		tok_symblist = list(word)

		for s in tok_symblist:
			
			if s not in self.valid_codepoint:
				#print("rejected char:", s, ord(s))
				return False

		return True


class AlphabetFilterUniqueCharacters(AbstractFilter):

	def __init__(self, lang, script, no_fail=False):

		self.lang = lang
		self.script = script

		if lang not in languagedb:
			raise Exception("Error: unsupported lang: "+lang)
		if script not in scriptdb:
			raise Exception("Error: unsupported script: "+script)

		scriptid = unicodedb.map_iso_idx[script]

		if [lang, script] not in alphabetdb:
			raise Exception("Error: unsupported lang/script pair"+ script)

		self.valid_characters = alphabetdb.getCharacters(lang, script)

		self.map_char_isuniq = {}
		for c in self.valid_characters:
			self.map_char_isuniq[c] = len(alphabetdb.map_char_lang[c]) == 1

	def __call__(self, t):
		return self.decide(t)

	def decide(self, s):

		tok_symblist = list(s)

		count_valid=0
		count_invalid=0

		for s in tok_symblist:
			
			if s in self.map_char_isuniq:
				if self.map_char_isuniq[s]:
					count_valid += 1
				else:
					count_invalid += 1
			else:
				return False, count_valid, count_invalid

		return (count_valid > 0, count_valid, count_invalid)	


from collections import Counter

class AlphabetFilterUncommonCharacters(AbstractFilter):

	def __init__(self, lang, script, no_fail=False):

		self.lang = lang
		self.script = script

		if lang not in languagedb:
			raise Exception("Error: unsupported lang: "+lang)
		if script not in scriptdb:
			raise Exception("Error: unsupported script: "+script)

		scriptid = unicodedb.map_iso_idx[script]

		if [lang, script] not in alphabetdb:
			raise Exception("Error: unsupported lang/script pair"+ script)

		self.valid_characters = alphabetdb.getCharacters(lang, script)

		self.resetCounter()

	def resetCounter(self):

		self.aggreg1 = Counter()
		self.aggreg2 = Counter()
		self.aggreg3 = Counter()
		self.aggreg4 = Counter()


	def __call__(self, t):
		return self.decide(t)

	def decide(self, word):

		tok_symblist = list(word)

		self.counter1 = Counter()
		self.counter2 = Counter()
		self.counter3 = Counter()
		self.counter4 = Counter()

		count_valid=0
		count_invalid=0

		for s in tok_symblist:
			
			if s in self.valid_characters:
				list_langs = alphabetdb.map_char_lang[s]
				count = len(list_langs)
				if count <= 4:
					for lang in list_langs:
						if count == 1:
							if lang not in self.counter1:
								self.counter1[lang] = 0
							self.counter1[lang] += 1
						if count == 2:
							if lang not in self.counter2:
								self.counter2[lang] = 0
							self.counter2[lang] += 1
						if count == 3:
							if lang not in self.counter3:
								self.counter3[lang] = 0
							self.counter3[lang] += 1
						if count == 4:
							if lang not in self.counter4:
								self.counter4[lang] = 0
							self.counter4[lang] += 1

		self.aggreg1.update(self.counter1)
		self.aggreg2.update(self.counter2)
		self.aggreg3.update(self.counter3)
		self.aggreg4.update(self.counter4)


		print("===", word)
		print(self.counter1.most_common())
		print(self.counter2.most_common())
		print(self.counter3.most_common())
		print(self.counter4.most_common())

		return (count_valid > 0, count_valid, count_invalid)	


	def decideOnAggregate(self):
		score = Counter()

		max = 4

		for lang, count in self.aggreg1.items():
			if lang not in score:
				score[lang] = 0
			score[lang] += count * (max-0)

		for lang, count in self.aggreg2.items():
			if lang not in score:
				score[lang] = 0
			score[lang] += count * (max-1)

		for lang, count in self.aggreg3.items():
			if lang not in score:
				score[lang] = 0
			score[lang] += count * (max-2)

		for lang, count in self.aggreg4.items():
			if lang not in score:
				score[lang] = 0
			score[lang] += count * (max-3)

		print("score:", score.most_common())

		if len(score) > 1 and len(set([x[1] for x in score.most_common()])) == 1:
			print("DRAW")
			return None

		return score.most_common(1)


import json
from nltk import ngrams

class NGramsFilter(AbstractFilter):

	def __init__(self, lang, script, n):
		self.lang = lang
		self.script = script
		self.models = json.load(open(lang+"_"+script+".charngram.dat"))
		self.n = n

	def __call__(self, t):
		return self.decide(t)

	def decide(self, s):
		if len(s) < self.n:
			return 0, 0, 0., 0.
		count_in=0
		count_out=0
		ng_freq = 0.
		lang_post = 0.
		all_ng  = ngrams(s.upper(), self.n)
		model = self.models[str(self.n)]
		for ng in all_ng:
			ng = "".join(ng)
			if ng not in model:
				count_out += 1
#				print("out,", ng)
			else:
				count_in += 1.
				ng_freq += model[ng]

		all_in = count_out == 0
		tot_ng = count_out + count_in

		return all_in, float(count_in)/float(tot_ng) if tot_ng > 0 else 0, ng_freq
	