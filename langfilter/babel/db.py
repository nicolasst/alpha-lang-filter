

import unicodedata
import configparser

import os

class Script:

	def __init__(self, name, iso, ucs_ranges, scriptocontinua, synonyms):
		self.name = name
		self.iso = iso
		self.ucs_ranges = ucs_ranges
		self.scriptocontinua = scriptocontinua
		self.synonyms = synonyms

	def __str__(self):
		return str(["Script", self.iso, self.name, self.ucs_ranges, self.scriptocontinua, self.synonyms])

class ScriptDB:

	def __init__(self):
		self.map_iso_script = {}
		self.map_iso_name = {}
		self.map_name_iso = {}

		self.read_data()

	def getScript(self, query):
		if query in self.map_iso_script:
			return self.map_iso_script[query]
		if query in self.map_name_iso:
			query = self.map_name_iso[query]
			return self.map_iso_script[query]

	def read_data(self):
		config = configparser.ConfigParser()
		config.read(os.path.dirname(os.path.realpath(__file__))+"/../data/static/scripts.ini")

		class MoveToBackException(Exception):
			pass

		list_scripts = config.sections()

		for lang_name in list_scripts:

			try:
				code = config[lang_name]["iso"]

				if "extends" not in config[lang_name]:
					ucs_ranges = config[lang_name]["ucs"].strip().split("\n")
					sc = "scriptocontinua" in config[lang_name]
				else:
					ucs_ranges = []
					for ext_code in config[lang_name]["extends"].split(", "):
						if ext_code not in self.map_iso_script:
							raise MoveToBackException
						ucs_ranges.extend(self.map_iso_script[ext_code].ucs_ranges)
						sc = self.map_iso_script[ext_code].scriptocontinua

				synonyms = config[lang_name]["synonym"].strip().split("\n") if "synonym" in config[lang_name] else []

				for code in code.split(", "):
					script = Script(lang_name, code, ucs_ranges, sc, synonyms)

					if code in self.map_iso_script:
						raise Exception("iso code already in database: "+code)

					self.map_iso_script[code] = script
					self.map_iso_name[code] = lang_name
					self.map_name_iso[lang_name] = code
			except MoveToBackException:
				list_scripts.append(lang_name)

	def getSupportedScripts(self):
		return self.map_iso_script.keys()

	def __str__(self):
		return str([str(x) for x in self.map_iso_script.values()])

	def __contains__(self, iso):
		return iso in self.map_iso_script


class MacroLanguage:

	def __init__(self, name, iso1, iso3, individuals, synonyms):
			self.name = name
			self.iso3 = iso3
			self.iso1 = iso1
			self.individuals = individuals
			self.synonyms = synonyms
	
class Language:

	def __init__(self, name, iso1, iso3, scripts, endonyms, synonyms):
		self.name = name
		self.iso3 = iso3
		self.iso1 = iso1
		self.scripts = scripts
		self.endonyms = endonyms
		self.synonyms = synonyms
		self.synonyms.append(name)

	def getScripts(self):
		return self.scripts

	def getEndonyms(self):
		return self.endonyms

	def getSynonyms(self):
		return self.synonyms

	def getName(self):
		return self.name

	def getIso3(self):
		return self.iso3

	def getIso1(self):
		return self.iso1

	def asTuple(self):
		return [ self.iso3, self.iso1, self.name, self.scripts, self.synonyms, self.endonyms]

	def __str__(self):
		return 	"\t".join([ (", ".join(d) if type(d) == list else d if d is not None else "") for d in self.asTuple() ])


class LanguageDB:

	def __init__(self):
		self.map_iso3_language = {}
		self.map_iso3_name = {}
		self.map_name_iso3 = {}
		self.map_iso1_iso3 = {}
		self.map_iso3_iso1 = {}

		self.read_data()

	def read_data(self):

		config = configparser.ConfigParser()
		config.read(os.path.dirname(os.path.realpath(__file__))+"/../data/static/languages.ini")

		list_languages = config.sections()

		for lang_name in list_languages:

			iso3 = config[lang_name]["iso3"]
			iso1 = config[lang_name]["iso1"] if "iso1" in config[lang_name] else None
			synonyms = config[lang_name]["synonym"].strip().split("\n") if "synonym" in config[lang_name] else []

			if "supergroup" not in config[lang_name]:
				scripts = config[lang_name]["script"].strip().split(", ")
				endonyms = config[lang_name]["endonym"].strip().split("\n") if "endonym" in config[lang_name] else []
				synonyms = config[lang_name]["synonym"].strip().split("\n") if "synonym" in config[lang_name] else []

				lang = Language(lang_name, iso1, iso3, scripts, endonyms, synonyms)
			else:
				pass

			if iso3 in self.map_iso3_language:
				raise Exception("iso already present in database: "+iso3)

			self.map_iso3_language[iso3] = lang
			self.map_iso3_iso1[iso3] = iso1
			self.map_iso1_iso3[iso1] = iso3
			self.map_iso3_name[iso3] = lang_name

			self.map_name_iso3[lang_name] = [iso3]

			for lang_syn in synonyms:
				if lang_syn not in self.map_name_iso3:
					self.map_name_iso3[lang_syn] = []
				if lang_syn not in self.map_name_iso3:
					self.map_name_iso3[lang_syn].append(iso3)

	def getSupportedLanguages(self):
		return self.map_iso3_language.keys()

	def getLang(self, query):
		iso3 = None
		if len(query) == 2 and (query.islower() or  query.isupper()):
			if query in self.map_iso1_iso3:
				iso3 = self.map_iso1_iso3[query]
		elif len(query) == 3 and (query.islower() or  query.isupper()):
			iso3 = query
			if query in self.map_name_iso3:
				list_iso3 = self.map_name_iso3[query]
				if len(list_iso3) > 1:
					raise Exception("Ambiguous language, parameter: "+query+", specify one of: "+str(list_iso3))
				else:
					iso3 = list_iso3[0]
		if iso3 is None:
			raise Exception("Invalid language parameter: "+query)

		return self.map_iso3_language[iso3]

	def __contains__(self, iso3):
		return iso3 in self.map_iso3_language

	def __str__(self):
		return str([str(x) for x in self.map_iso3_language])

class AlphabetDB:

	def __init__(self):

		self.map_lang_script_codepoints = {}
		self.map_lang_script_characters = {}

		self.map_char_lang = {}

		self.read_data()

	def read_data(self):

		config = configparser.ConfigParser()
		config.read(os.path.dirname(os.path.realpath(__file__))+"/../data/static/alphabets.ini")

		list_sections = config.sections()

		for section in list_sections:
			lang_iso, script_iso = section.split(", ")
			if lang_iso not in self.map_lang_script_codepoints:
				self.map_lang_script_codepoints[lang_iso] = {}
				self.map_lang_script_characters[lang_iso] = {}
			codepoints = config[section]["codepoints"].strip().split()
			codepoints = [int(x, 16) for x in codepoints]
			self.map_lang_script_codepoints[lang_iso][script_iso] = codepoints
			characters = [chr(x) for x in codepoints]
			self.map_lang_script_characters[lang_iso][script_iso] = characters

			for char in characters:
				if char not in self.map_char_lang:
					self.map_char_lang[char] = set()
				self.map_char_lang[char].add(lang_iso)

	def getCodepoints(self, lang, script):
		return self.map_lang_script_codepoints[lang][script]

	def getCharacters(self, lang, script):
		return self.map_lang_script_characters[lang][script]

	def getSupportedAlphabets(self):
		alphabets = []
		for lang in self.map_lang_script_characters:
			for script in self.map_lang_script_characters[lang]:
				alphabets.append((lang, script, len(self.map_lang_script_characters[lang][script])))
		return alphabets

	def __str__(self):
		return str(self.map_lang_script_codepoints) + str(self.map_lang_script_characters) + str(self.map_char_lang)

	def __contains__(self, query):
		if type(query) == list:
			lang, script = query
			return lang in self.map_lang_script_characters and script in self.map_lang_script_characters[lang]
		else:
			raise Exception("wrong arguments to function")

class UnicodeDB:

	def __init__(self):
		self.highest_codepoint = 1114111

		self.map_iso_idx={}
		self.map_idx_iso={}

		self.map_name_iso = {}
		self.map_iso_name = {}

		self.map_codepoint_idx = [-1] * self.highest_codepoint
		self.map_codepoint_blockidx = {}
		self.map_codepoint_category = {}

		self.set_valid_codepoints = set()

		self.map_blockname_codepoint = {}
		self.map_blockname_iso = {}
		self.map_blockidx_blockname = {}

		self.read_unicode_codepoints()
		self.read_property_aliases()
		self.read_unicode_blocks()
		self.read_unicode_scripts()

	def lookup(self, query):

		if query in self.map_iso_idx:
			return ["script", query, self.map_iso_name[query] ]

	def read_unicode_codepoints(self, fname=os.path.dirname(os.path.realpath(__file__))+"/../data/unicode/UnicodeData.txt"):
	
		interval_start=None

		with open(fname) as f:
			for line in f:
				idx = line.index(";")
				idx2 = line.index(";", idx+1)
				idx3 = line.index(";", idx2+1)

				value = line[:idx]
				value = int(value, 16)

				category = line[idx2+1:idx3]

				if interval_start is not None:
					interval_end = value
					for i in range(interval_start, interval_end):
						self.set_valid_codepoints.add(i)
						self.map_codepoint_category[i] = category
					interval_start = None
				else:
					if line[idx+1] != "<" or line[idx2-6:idx2] != "First>":
						self.set_valid_codepoints.add(value)
						self.map_codepoint_category[value] = category
					else:
						interval_start = value

	def read_property_aliases(self, fname=os.path.dirname(os.path.realpath(__file__))+"/../data/unicode/PropertyValueAliases.txt"):

		f = open(fname)
	
		count=0	
		state=0
		for line in f.readlines():
			line = line.strip()
			if len(line) <= 1: 
				continue
			elif line == "# Script (sc)":
				state = 1
				continue
			elif line == "# Block (blk)":
				state = 2
				continue
			elif line[0] == '#':
				if state == 2:
					state = 0
				if state == 1:
					break
				continue

			if state == 1:
				line = line.split()
				script_name = line[4]
				script_iso = line[2]
				self.map_name_iso[script_name] = script_iso
				self.map_iso_name[script_iso] = script_name
				self.map_iso_idx[script_iso] = count
				self.map_idx_iso[count] = script_iso
				count = count + 1
			elif state == 2:
				pass
		f.close()

	def read_unicode_blocks(self, fname=os.path.dirname(os.path.realpath(__file__))+"/../data/unicode/Blocks.txt"):

		count = 0

		f = open(fname)
		for line in f.readlines():
			line = line.strip()
			if len(line) <= 1: 
				continue

			if len(line) > 1:
				if line[0] == '#':
					continue

				line = line.split(";")
				line_range = line[0]
				line_script = line[1][1:]

				line_range = line_range.split("..")
				val1=int(line_range[0],base=16)
				val2=int(line_range[1],base=16)

				self.map_blockname_codepoint[line_script] = []
				for val in range(val1,val2+1):
					if val in self.set_valid_codepoints:
						self.map_blockname_codepoint[line_script].append(chr(val))
						self.map_codepoint_blockidx[val] = count

				self.map_blockidx_blockname[count] = line_script
				count += 1

		f.close()

	def read_unicode_scripts(self, fname=os.path.dirname(os.path.realpath(__file__))+"/../data/unicode/Scripts.txt"):

		f = open(fname)
		for line in f.readlines():
			line = line.strip()
			if len(line) <= 1: 
				continue
			if line[0] == '#':
				continue
			line = line.split()
			line_range = line[0]
			line_script = line[2]

			if line_script in self.map_name_iso:
				scriptiso = self.map_name_iso[line_script]
				curscriptid = self.map_iso_idx[scriptiso]
			else:
				curscriptid = 0
						
			if ".." not in line_range:
				val=int(line_range,base=16)
				self.map_codepoint_idx[val] = curscriptid
			else:
				line_range = line_range.split("..")
				val1=int(line_range[0],base=16)
				val2=int(line_range[1],base=16)
				for val in range(val1,val2+1):
					self.map_codepoint_idx[val] = curscriptid
		f.close()

	def getBlockCharacters(self, block_name, category=None):
		characters = [x for x in self.map_blockname_codepoint[block_name] if category is None or self.map_codepoint_category[x] in category]
		#characters = [chr(codepoint) for codepoint in self.map_blockname_codepoint[block_name]]
		return characters

	def getBlockLetters(self, block_name):
		characters = [x for x in self.map_blockname_codepoint[block_name] if unicodedata.category(x)[0] == "L"]
		#characters = [chr(codepoint) for codepoint in self.map_blockname_codepoint[block_name]]
		return characters

	def getSupportedBlocks(self):
		blocks = []
		for blockname in self.map_blockname_codepoint.keys():
			blocks.append((blockname, len(self.map_blockname_codepoint[blockname])))
		return blocks

	def __str__(self):
		return 		str(self.map_codepoint_idx) + "\n"  + \
		str(self.map_name_iso) + "self.map_name_iso\n"  + \
		str(self.map_iso_name) + "self.map_iso_name\n"  + \
		str(self.map_iso_idx) + "self.map_iso_idx\n"  + \
		str(self.map_idx_iso) + "self.map_idx_iso\n"  + \
		str(self.map_blockname_codepoint) + "self.map_blockname_codepoint\n"  + \
		str(self.set_valid_codepoints) + "self.set_valid_codepoints\n"  + \
		str(self.map_codepoint_category) + "map_codepoint_category\n"  + \
		str(self.map_blockidx_blockname) + "map_blockidx_blockname\n"  + \
		str(self.map_codepoint_blockidx) + "map_codepoint_blockidx"


scriptdb = ScriptDB()

#print(scriptdb)


languagedb = LanguageDB()

#print(languagedb)

alphabetdb = AlphabetDB()

#print(alphabetdb)


unicodedb = UnicodeDB()

#print(unicodedb)

if __name__ == "__main__":

	map_1lang_chars = {}

	for char, list_iso in alphabetdb.map_char_lang.items():
		if len(list_iso) == 1:
			for lang in list_iso:
				if lang not in map_1lang_chars:
					map_1lang_chars[lang] = []
				map_1lang_chars[lang].append(char)

	for lang, chars in map_1lang_chars.items():
		print(lang, len(chars))

	print(unicodedb.map_blockname_codepoint.keys())

	print(languagedb.map_name_iso3)