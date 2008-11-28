from sgmllib import SGMLParser
import urllib

def sztakidict(lang, word):
	class myurlopener(urllib.FancyURLopener):
		version = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.2) Gecko/20070225 Firefox/2.0.0.2"

	class HTMLParser(SGMLParser):
		def reset(self):
			SGMLParser.reset(self)
			self.inspan = False
			self.inme = False
			self.mes = []

		def start_span(self, attrs):
			for k, v in attrs:
				if k == "class" and v == "normtext":
					self.inspan = True

		def end_span(self):
			if self.inspan:
				self.inspan = False

		def handle_comment(self, text):
			if text == "me" and self.inspan:
				self.inme = True
			elif text == "/me":
				self.inspan = False

		def handle_data(self, text):
			if self.inspan and self.inme:
				s = text.strip()
				if len(s) and s != ";":
					self.mes.append(s)

	urllib._urlopener = myurlopener()
	sock = urllib.urlopen("http://szotar.sztaki.hu/dict_search.php?" + urllib.urlencode({'L':lang, 'W':word, 'C':'1'}))
	page = sock.read()
	sock.close()

	parser = HTMLParser()
	parser.reset()
	parser.feed(page)
	parser.close()

	return parser.mes

def helper(lang, word):
	dicts = {
			"en2hu": "ENG:HUN:EngHunDict",
			"hu2pl": "HUN:POL:PolHunDict",
			"hu2en": "HUN:ENG:EngHunDict",
			"nl2hu": "HOL:HUN:HolHunDict",
			"de2hu": "GER:HUN:GerHunDict",
			"fr2hu": "FRA:HUN:FraHunDict",
			"it2hu": "ITA:HUN:ItaHunDict",
			"hu2de": "HUN:GER:GerHunDict",
			"hu2it": "HUN:ITA:ItaHunDict",
			"hu2nl": "HUN:HOL:HolHunDict",
			"hu2fr": "HUN:FRA:FraHunDict",
			"pl2hu": "POL:HUN:PolHunDict"
			}
	if lang == "hu":
		lang += "2en"
	elif "2" not in lang:
		lang += "2hu"
	try:
		return "%s: %s" % (word, "; ".join(sztakidict(dicts[lang], word)))
	except KeyError:
		return "no such dict"

if __name__ == "__main__":
	import sys
	print helper(sys.argv[1], " ".join(sys.argv[2:]))
