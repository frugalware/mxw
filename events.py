import traceback, inspect, sys, password, time, urllib, re, pickle, popen2
sys.path.append("/usr/lib")
import feedparser, htmlentitydefs, random
from xml.dom import minidom
from sgmllib import SGMLParser

class Rss:
	def __init__(self, url, target, title):
		self.url = url
		self.target = target
		self.title = title
		self.feed = None
		self.updated = time.time()

class config:
	server = "irc.freenode.net"
	port = 6667
	nick  = "mxw_"
	password = password.password
	realname = "yeah"
	channels = ['#frugalware', '#frugalware.dev', '#frugalware.hu', '#frugalware.fr', '#debian.hu']
	authors = "/home/ftp/pub/frugalware/frugalware-current/docs/xml/authors.xml"
	# for reporting bugs
	owner = "vmiklos"

	feeds = [Rss("http://frugalware.org/rss/packages", "#frugalware", "packages"),
			Rss("http://frugalware.org/rss/blogs", "#frugalware", "blogs"),
			Rss("http://frugalware.org/rss/bugs", "#frugalware.dev", "bugs"),
			Rss("http://frugalware.org/~vmiklos/ping2rss/ping2rss.py", "#frugalware.dev", "ping")]
	duped_feeds = "feeds"
	database = {
			":)": ":D",
			":D": "lol",
			"bugs": "here we can help, but if you want a bug/feature to be fixed/implemented, then please file a bugreport/feature request at http://bugs.frugalware.org",
			"rtfm": "if you're new to Frugalware, then before asking please read our documentation at http://frugalware.org/docs/, probably your question is answered there",
			"flame": "Frugalware is best! All other distros suck! Oh, sure, we plan to take over the world any minute now ;)",
			"dance": "0-<\n0-/\n0-\\"
			}

todo = {}

##
# functions used by event handlers
##
def command(self, c, source, target, data):
	argv = data.split(' ')
	ret = []
	# operator commands
	if argv[0] == "opme":
		cmd = 'c.mode("%s", "+o %s")' % (target, source)
		safe_eval(source, cmd, c)
	elif argv[0] == "voiceme":
		cmd = 'c.mode("%s", "+v %s")' % (target, source)
		safe_eval(source, cmd, c)
	elif argv[0] == "devoiceme":
		cmd = 'c.mode("%s", "-v %s")' % (target, source)
		safe_eval(source, cmd, c)
	elif argv[0] == "voice":
		if len(argv) < 2:
			c.privmsg(target, "%s: 'voice' requires a parameter (nick)" % source)
			return
		cmd = 'c.mode("%s", "+v %s")' % (target, argv[1])
		safe_eval(source, cmd, c)
	elif argv[0] == "devoice":
		if len(argv) < 2:
			c.privmsg(target, "%s: 'devoice' requires a parameter (nick)" % source)
			return
		cmd = 'c.mode("%s", "-v %s")' % (target, argv[1])
		safe_eval(source, cmd, c)
	elif argv[0] == "kick":
		if len(argv) < 3:
			c.privmsg(target, "%s: 'kick' requires two parameter (nick, reason)" % source)
			return
		cmd = 'c.kick("%s", "%s", "%s")' % (target, argv[1], argv[2])
		safe_eval(source, cmd, c)
	elif argv[0] == "topic":
		if len(argv) < 2:
			c.privmsg(target, "%s: 'topic' requires a parameter (new topic)" % source)
			return
		cmd = 'c.topic("%s", "%s")' % (target, " ".join(argv[1:]))
		safe_eval(source, cmd, c)
	# end of operator commands
	# web services
	elif argv[0] == "google":
		google(c, source, target, argv[1:])
	elif len(argv) > 3 and re.match("^[0-9.]+[KM]? [a-z]+ in [a-z]+$", " ".join(argv[:4])):
		xe(c, source, target, argv)
	elif argv[0] == "lc":
		lc(c, source, target)
	# end of web services
	# cmdline frontend commands
	elif argv[0] == "calc":
		calc(c, source, target, argv[1:])
	# misc
	elif argv[0] == "reload":
		self.reload()
		c.privmsg(target, "%s: reload done" % source)
	elif argv[0] == "eval":
		safe_eval(source, " ".join(argv[1:]), c)
	# database commands
	elif argv[0] in config.database.keys():
		record = config.database[argv[0]]
		if "\n" in record or " " not in record:
			for i in record.split("\n"):
				c.privmsg(target, "%s" % i)
		else:
			c.privmsg(target, "%s: %s => %s" % (source, argv[0], config.database[argv[0]]))
	else:
		c.privmsg(target, "%s: '%s' is not a valid command" % (source, argv[0]))

def calc(c, source, target, data):
	input = " ".join(data)
	pout, pin = popen2.popen2("bc")
	pin.write("scale=2;%s\n" % input)
	pin.close()
	ret = "".join(pout.readlines()).strip()
	pout.close()
	if len(ret):
		if ret[0] == ".":
			ret = "0" + ret
		c.privmsg(target, "%s=%s" % (input, ret))
	else:
		c.privmsg(target, "parse error")

def google(c, source, target, data):
	class myurlopener(urllib.FancyURLopener):
		version = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.2) Gecko/20070225 Firefox/2.0.0.2"

	class HTMLParser(SGMLParser):
		def reset(self):
			SGMLParser.reset(self)
			self.inh2 = False
			self.indesc = False
			self.titles = []
			self.title = []
			self.descs = []
			self.desc = []
			self.links = []
			self.link = None

		def start_h2(self, attrs):
			for k, v in attrs:
				if k == "class" and v == "r":
					self.inh2 = True

		def start_td(self, attrs):
			for k, v in attrs:
				if k == "class" and v == "j":
					self.indesc = True

		def end_h2(self):
			self.titles.append("".join(self.title))
			self.title = []
			self.links.append(self.link)
			self.link = None
			self.inh2 = False

		def start_br(self, attrs):
			if self.indesc:
				self.descs.append("".join(self.desc))
				self.desc = []
				self.indesc = False

		def start_a(self, attrs):
			if self.inh2 and not self.link:
				for k, v in attrs:
					if k == "href":
						self.link = v

		def handle_data(self, text):
			if self.inh2:
				self.title.append(text)
			elif self.indesc:
				self.desc.append(text)

	if len(data) < 1:
		c.privmsg(target, "%s: 'google' requires a parameter (search term)" % source)
		return
	urllib._urlopener = myurlopener()
	sock = urllib.urlopen("http://www.google.com/search?" + urllib.urlencode({'q':" ".join(data)}))
	page = sock.read()
	sock.close()

	parser = HTMLParser()
	parser.reset()
	parser.feed(page)
	parser.close()

	c.privmsg(target, parser.titles[0])
	c.privmsg(target, parser.descs[0])
	c.privmsg(target, parser.links[0])

def xe(c, source, target, opts):
	class myurlopener(urllib.FancyURLopener):
		version = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.2) Gecko/20070225 Firefox/2.0.0.2"

	class HTMLParser(SGMLParser):
		def handle_data(self, text):
			if text.startswith("1 %s = " % self.fro):
				self.ret = text

	urllib._urlopener = myurlopener()
	amount = opts[0]
	fro = opts[1].upper()
	to = opts[3].upper()

	if amount[-1] == "K":
		amount = float(amount[:-1])*1000
	elif amount[-1] == "M":
		amount = float(amount[:-1])*1000000

	# wtf this is always 1
	data = urllib.urlencode({'Amount':1, 'From':fro,'To':to})
	sock = urllib.urlopen('http://www.xe.com/ucc/convert.cgi', data)

	parser = HTMLParser()
	parser.fro = fro
	parser.reset()
	parser.feed(sock.read())
	ret = re.sub('.* = ', '', parser.ret).lower().split(' ')
	c.privmsg(target, "%.3lf %s" % (float(ret[0])*float(amount), ret[1]))
	parser.close()
	sock.close()

def lc(c, source, target):
	class HTMLParser(SGMLParser):
		def start_img(self, attrs):
			for k, v in attrs:
				if k == "alt":
					self.state = v

	sock = urllib.urlopen('http://dawn.royalcomp.hu/~raas/lc.html')

	parser = HTMLParser()
	parser.reset()
	parser.feed(sock.read())
	for i in htmlentitydefs.entitydefs:
		parser.state = re.sub('&%s;' % i, htmlentitydefs.entitydefs[i], parser.state)
	c.privmsg(target, "Gratulalunk, Te is porgettel egyet a LAMMERSZAMLALON! %s" % parser.state)
	parser.close()
	sock.close()

def check_rss(self, c, e):
	current = time.time()
	for i in config.feeds:
		gray = i.title
		i.feed = feedparser.parse(i.url)
		for j in i.feed.entries:
			target = i.target
			if time.mktime(j.updated_parsed) > i.updated:
				#c.privmsg("#fdb", "new rss entry!")
				if i.title == "packages":
					brown = j.author.split('@')[0]
					green = j.title
					if brown == "syncpkgd":
						target = "#frugalware.dev"
				elif i.title == "ping":
					brown = j.author
					green = j.title
				else: # blogs and bugs
					brown = j.title
					green = j.link
				c.privmsg(target, "14%s7 %s3 %s" % (gray, brown, green))
				# to avoid floods
				time.sleep(2)
		if len(i.feed.entries):
			i.updated = time.mktime(i.feed.entries[0].updated_parsed)
		else:
			c.privmsg(config.owner, "the '%s' feed is empty" % (i.title))

def inxml(nick):
	xmldoc = minidom.parse(config.authors)
	for i in xmldoc.getElementsByTagName('author'):
		if unicode(nick) == i.getElementsByTagName("nick")[0].firstChild.toxml():
			return True
	return False

def safe_eval(nick, cmd, c):
	global todo

	if not inxml(nick):
		return
	if nick in todo.keys():
		todo[nick].append(cmd)
	else:
		todo[nick] = [cmd]
	c.whois([nick])

##
# the event handlers
##
def on_welcome(self, c, e):
	c.privmsg("nickserv", "ghost %s %s" % (config.nick, config.password))
	time.sleep(2)
	c.nick(config.nick)
	c.privmsg("nickserv", "identify %s" % config.password)
	time.sleep(2)
	for i in config.channels:
		c.join(i)

def on_privmsg(self, c, e):
	nick = e.source().split("!")[0]
	command(self, c, nick, nick, e.arguments()[0])

def on_pubmsg(self, c, e):
	source = e.source().split("!")[0]
	# highlight
	if e.arguments()[0].startswith(c.get_nickname()):
		data = e.arguments()[0][len(c.get_nickname()):]
		if data[:1] == "," or data[:1] == ":":
			data = data[1:]
		command(self, c, source, e.target(), data.strip())
	# trigger
	elif e.target() == "#frugalware" and " ... " in e.arguments()[0]:
		c.privmsg(e.target(), """%s: using "..." so much isn't polite to other users. please consider changing that habit.""" % source)
	elif e.target()[-3:] == ".hu" and re.match("^haszn..?l valaki", e.arguments()[0]):
		c.privmsg(e.target(), "nem, viccbol van belole csomag")
	elif e.target()[-3:] == ".hu" and e.arguments()[0] == "yepp!":
		sock = open("akii-fun.lines")
		lines = sock.readlines()
		sock.close()
		c.privmsg(e.target(), "Yepp! %s" % random.choice(lines))
	elif e.arguments()[0] == "yow!":
		sock = open("yow.lines")

		lines = "".join(sock.readlines()).split("\000\n")
		sock.close()
		out = "Yow! %s" % random.choice(lines).strip()
		for i in out.split("\n"):
			c.privmsg(e.target(), i)

def on_bug(self, c, e):
	type, value, tb = sys.exc_info()
	stype = str(type).split("'")[1]
	print "Traceback (most recent call last):"
	print "".join(traceback.format_tb(tb)).strip()
	print "%s: %s" % (stype, value)

	badline = inspect.trace()[-1]
	c.privmsg(config.owner, "%s at file %s line %d" % (stype, badline[1], badline[2]))

def on_join(self, c, e):
	if e.target() == "#frugalware.dev":
		nick = e.source().split("!")[0]
		cmd = 'c.mode("%s", "+v %s")' % (e.target(), nick)
		safe_eval(nick, cmd, c)

def on_identified(self, c, e):
	global todo

	nick = e.arguments()[0]
	if nick not in todo.keys():
		return
	eval(todo[nick][-1])
	del todo[nick]

def on_ping(self, c, e):
	check_rss(self, c, e)
