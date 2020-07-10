#!/usr/bin/python3
import argparse
import sys
import unicodedata
from collections import namedtuple

import sys
import os
import re

from langfilter.babel.db import scriptdb, languagedb, alphabetdb, unicodedb
from langfilter.babel.filters import AlphabetFilter, NGramsFilter, UnicodeFilter, AlphabetFilterUniqueCharacters, AlphabetFilterUncommonCharacters


def tokenize(x):
	return x.split()

def untokenize(x):
	return " ".join(x)

def remove_affix_punctuation(word):
	while len(word) > 0 and unicodedata.category(word[0])[0] == "P":
		word = word[1:]

	while len(word) > 0 and unicodedata.category(word[-1])[0] == "P":
		word = word[:-1]

	return word

class LanguageFilter:

	def __init__(self, args):
		self.args = args

		self.default_filter = not self.args.ab and \
						not self.args.ab_uniq and \
						not self.args.ab_uncommon and \
						not self.args.ucs

		if self.default_filter:
			if [self.args.lang, self.args.script] in alphabetdb:
				self.filter = AlphabetFilter(self.args.lang, self.args.script)
			else:
				self.filter = UnicodeFilter(self.args.script, self.args.verbose)

		if self.args.ab:
			self.filter = AlphabetFilter(self.args.lang, self.args.script)
		if self.args.ab_uniq:
			self.filter = AlphabetFilterUniqueCharacters(self.args.lang, self.args.script)
		if self.args.ab_uncommon:
			self.filter = AlphabetFilterUncommonCharacters(self.args.lang, self.args.script)
		if self.args.ucs:
			self.filter = UnicodeFilter(self.args.script, self.args.verbose)

	def accept_word(self, x):
		return self.filter.decide(x)

	def output_line(self, line, out=sys.stdout):
		if line:
			if self.args.remove_non_alphanum:
				line = re.sub(r"[^\w'-]+", " ", line, flags=re.UNICODE)
			print(line, file=out)

	def process_file(self, f):
		with open(f) as f:
			self.process_stream(f)

	def process_stream(self, stream):

		for line in stream:
			line = line.rstrip("\n")

			tokens = tokenize(line)

			tokens_accepted = [ self.accept_word(remove_affix_punctuation(tok)) for tok in tokens]

			if not self.args.words:
				accept_line = (float(len(tokens_accepted)) / len(tokens) >= self.args.prop) != self.args.reverse
				if accept_line:
					self.output_line(line)
				continue
			else:
				tokens_filtered = [ tok if not self.args.replace else self.args.replace for tok, accepted in zip(tokens, tokens_accepted) if accepted != self.args.reverse ]
				line_filtered = untokenize(tokens_filtered)
				self.output_line(line_filtered)
				continue

def normalizeLinguisticParameters(lang, script):

	if lang is None and script is None:
		print("error: missing lang or script")
		sys.exit(1)
	
	if lang is not None:
		if lang != "_" and lang != "":
			try:
				lang = languagedb.getLang(lang).getIso3()
			except Exception as e:
				print(e)
				sys.exit(0)


	if script is not None:

		if ( script != "default" and script != "_" and script != ""):
			script = script
		else:
			list_scripts = languagedb.getLang(lang).getScripts()
			if len(list_scripts) == 1:
					script = list_scripts[0]
			else:
				print(" ".join(["Ambiguous script for lang", lang, "please specify one script among: ", ", ".join(list_scripts)]))
				sys.exit(1)

	return lang, script


def main():
	parser = argparse.ArgumentParser(description="filter input based on target language or script")

	parser.add_argument("--filter", help="filter text by language (uses ab if availble otherwise ucs)", action="store_true")
	#parser.add_argument("--detect", help="detect langauge of text", action="store_true")

	parser.add_argument("-l", "--lang", help="language (underscore to ignore)", nargs='?', const="")
	parser.add_argument("-s", "--script", help="script (underscore to ignore)", nargs='?', const="")

	# selection options
	parser.add_argument("-w", "--words", help="filter out words instead of lines", action="store_true")
	parser.add_argument("-r", "--reverse", help="reverse filtering", action="store_true")
	
	# filtering options
	parser.add_argument("--replace", help="replace deleted words with special token", nargs='?')
	parser.add_argument("--highlight", help="highlight matched words with special token", action="store_true")

	# detection options
	parser.add_argument("-p", "--prop", help="proportion of target word to accept whole line", nargs='?', default=1.)

	# misc option
	parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")


	parser.add_argument("--strict-alpha", help="accept only letters and spaces", action="store_true")
	parser.add_argument("--remove-non-alphanum", help="supress non alphabumeric characters from output", action="store_true")

	# processing options
	parser.add_argument("--ab", help="filter out words using alphabet", action="store_true")
	parser.add_argument("--ab-uniq", help="filter out words using uniq letters", action="store_true")
	parser.add_argument("--ab-uncommon", help="filter out words using uncomon letters", action="store_true")

	parser.add_argument("--ucs", help="filter out words using unicode ranges of the script", action="store_true")

	parser.add_argument("--ng", help="filter out words using ngrams", action="store_true")

	parser.add_argument("--model", help="model file (ngrams)")

	# info options
	parser.add_argument("--list-ab", help="display supported languages/script for alphabet filtering", action="store_true")
	parser.add_argument("--list-ucs", help="display supported scripts for unicode filtering", action="store_true")
	#parser.add_argument("--list-ng", help="display supported languages/script for ngrams filtering", action="store_true")

	parser.add_argument("--list-ab-letters", help="display letters of given alphabet", action="store_true")
	parser.add_argument("--list-ucs-letters", help="display letters of given unicode block", action="store_true")

	parser.add_argument("--list-langs", help="display info on all supported languages", action="store_true")
	parser.add_argument("--info", help="display info on given languages/script", action="store_true")

	parser.add_argument("--identify-char", help="identify character", action="store_true")

	parser.add_argument("file", help="files", nargs='*')

	args = parser.parse_args()


	if args.identify_char:
		c = sys.stdin.readline()[0]
		codepoint = ord(c)
		category = unicodedata.category(c)
		script_id = unicodedb.map_codepoint_idx[codepoint]

		try:
			name = unicodedata.name(c)
		except:
			name = "UNDEFINED"
		print(	"char:", c,
				"codepoint:", codepoint,
				"unicode range index:", script_id,
				"unicode range name:", unicodedb.map_blockidx_blockname[unicodedb.map_codepoint_blockidx[codepoint]],
				"category:", category,
				"name:", name)
		sys.exit(0)

	if args.list_langs:
		langs = languagedb.getSupportedLanguages()
		for lang in langs:
			print(languagedb.getLang(lang))
		sys.exit(0)

	lang = args.lang
	script = "default" if args.lang and not args.script else args.script if args.script else None

	lang, script = normalizeLinguisticParameters(lang, script)

	if args.verbose:
		print("processing: {} {}".format(lang, script))

	args.lang = lang
	args.script = script

	if args.info:
		print(languagedb.getLang(args.lang))
		sys.exit(0)

	if args.list_ab:
		for data in alphabetdb.getSupportedAlphabets():
			print("\t".join([str(x) for x in data]))
		sys.exit(0)

	if args.list_ab_letters:
		characters = alphabetdb.getCharacters(lang, script)
		print("\n".join([ ("%04x" % ord(c))+"\t"+c for c in characters]))
		sys.exit(0)

	if args.list_ucs:
		for data in unicodedb.getSupportedBlocks():
			print("\t".join([str(x) for x in data]))
		sys.exit(0)

	if args.list_ucs_letters:
		characters = unicodedb.getBlockLetters(script)
		print("\n".join([ ("%04x" % ord(c))+"\t"+c for c in characters]))
		sys.exit(0)



	lang_filter = LanguageFilter(args)

	if len(args.file) > 0:
		for file in args.file:
			lang_filter.process_file(file)
	else:
			lang_filter.process_stream(sys.stdin)

if __name__ == "__main__":

#	import cProfile
#	cProfile.run("main()")

	main()
