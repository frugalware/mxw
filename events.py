import traceback, inspect, sys, password, time, urllib, re, pickle
sys.path.append("/usr/lib")
import feedparser, htmlentitydefs, random, os, threading, string, glob
import anydatetime, socket
from xml.dom import minidom
from sgmllib import SGMLParser
from irclib import Event
import sztakidict
import urllib2

sys = reload(sys)
sys.setdefaultencoding("utf-8")

class Rss:
	def __init__(self, url, targets, title):
		self.url = url
		self.targets = targets
		self.title = title
		self.feed = None
		self.updated = time.time()

class RssThread(threading.Thread):
	def __init__(self, s, c, e):
		threading.Thread.__init__(self)
		self.s = s
		self.c = c
		self.e = e
		self.dieplz = False
		self.lastcheck = 0
	def run(self):
		while(True):
			if self.dieplz:
				break
			time.sleep(180)
			check_rss(self.s, self.c, self.e)
			self.lastcheck = time.time()

class NotifyThread(threading.Thread):
	def __init__(self, c):
		threading.Thread.__init__(self)
		self.c = c
	def run(self):
		while(True):
			time.sleep(60)
			for i in self.todo:
				nick, t, text, target, source = i
				if time.time() > time.mktime(t):
					self.c.privmsg(target, "%s: %s (requested by %s)" % (nick, text, source))
					self.todo.remove(i)

class SockThread(threading.Thread):
	def __init__(self, c):
		threading.Thread.__init__(self)
		self.c = c
	def run(self):
		c = self.c
		server = socket.socket ( socket.AF_UNIX, socket.SOCK_DGRAM )
		if os.path.exists("mxw2.sock"):
			os.remove("mxw2.sock")
		server.bind ("mxw2.sock")
		os.chmod("mxw2.sock", 0777)
		while True:
			buf = server.recv(1024)
			if not buf:
				continue
			for i in buf.split("\n"):
				eval(compile(i, "eval", "single"))

##
# functions used by commands
##
def sendsms(c, source, target, number, message):
	ret = os.system("~/bin/baratikor-sms -a vmiklos@vmiklos.hu %s %s" % (number, message))
	if ret == 0:
		c.privmsg(target, "%s: sent!" % source)
	else:
		c.privmsg(target, "%s: sth went wrong ;/" % source)

def sms(c, source, target, argv):
	"""sends sms. example: 'sms 30301234567 foo bar'"""
	if len(argv)<2:
		sock = os.popen("~/bin/baratikor-sms -a vmiklos@vmiklos.hu -b 2>/dev/null")
		buf = sock.read()
		sock.close()
		b = re.sub(r".*: (.*),.*", r"\1", buf)
		c.privmsg(target, "%s: 'sms' requires two parameters (number, message). current balance: %s" % (source, b))
		return
	safe_eval(source, 'sendsms(c, "%s", "%s", "%s", "%s")' % (source, target, argv[0], " ".join(argv[1:])), c)

def wtf(c, source, target, argv):
	"""resolves an abbreviation. requires one parameter: the abbreviation to resolve. falls back to 'define' (you can improve the db at /pub/other/people/vmiklos/mxw/acronyms!)"""
	if len(argv)<1:
		c.privmsg(target, "%s: 'wtf' requires a parameter" % source)
		return
	f = None
	if os.path.exists("acronyms"):
		f = "acronyms"
	elif os.path.exists("../acronyms"):
		f = "../acronyms"
	sock = os.popen("wtf -f %s %s" % (f, argv[0]))
	buf = sock.readline().strip()
	sock.close()
	if buf != "%s: nothing appropriate" % argv[0]:
		c.privmsg(target, "%s: %s" % (source, buf))
	else:
		define(c, source, target, argv)

def choose(c, source, target, argv):
	"""chooses a random value from a list. example: choose foo bar"""
	if len(argv)<2:
		c.privmsg(target, "%s: 'choice' requires multiple parameters" % source)
		return
	c.privmsg(target, "%s: %s" % (source, random.choice(argv)))

def opme(c, source, target, argv):
	"""gives operator status to you on the current channel"""
	safe_eval(source, 'c.mode("%s", "+o %s")' % (target, source), c)

def op(c, source, target, argv):
	"""gives operator status to somebody on a channel. optional second parameter: channel (defaults to current)"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'op' requires a parameter (nick)" % source)
		return
	if len(argv) < 2:
		chan = target
	else:
		chan = argv[1]
	cmd = 'c.mode("%s", "+o %s")' % (chan, argv[0])
	safe_eval(source, cmd, c)

def deop(c, source, target, argv):
	"""takes operator status from somebody on the current channel"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'deop' requires a parameter (nick)" % source)
		return
	cmd = 'c.mode("%s", "-o %s")' % (target, argv[0])
	safe_eval(source, cmd, c)

def voiceme(c, source, target, argv):
	"""gives voice to you on the a channel. optional parameter: channel (defaults to current)"""
	if len(argv) < 1:
		chan = target
	else:
		chan = argv[0]
	safe_eval(source, 'c.mode("%s", "+v %s")' % (chan, source), c)

def devoiceme(c, source, target, argv):
	"""takes voice from you on the current channel"""
	safe_eval(source, 'c.mode("%s", "-v %s")' % (target, source), c)

def voice(c, source, target, argv):
	"""gives voice to somebody on a channel. optional second parameter: channel (defaults to current)"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'voice' requires a parameter (nick)" % source)
		return
	if len(argv) < 2:
		chan = target
	else:
		chan = argv[1]
	cmd = 'c.mode("%s", "+v %s")' % (chan, argv[0])
	safe_eval(source, cmd, c)

def devoice(c, source, target, argv):
	"""takes voice from somebody on the current channel"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'devoice' requires a parameter (nick)" % source)
		return
	cmd = 'c.mode("%s", "-v %s")' % (target, argv[0])
	safe_eval(source, cmd, c)

def kick(c, source, target, argv):
	"""kicks somebody from the current channel with a reason"""
	if len(argv) < 2:
		c.privmsg(target, "%s: 'kick' requires two parameter (nick, reason)" % source)
		return
	cmd = 'c.kick("%s", "%s", "%s")' % (target, argv[0], " ".join(argv[1:]))
	safe_eval(source, cmd, c)

def ban(c, source, target, argv):
	"""bans somebody from the current channel"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'ban' requires a parameter (mask)" % source)
		return
	cmd = 'c.mode("%s", "+b %s")' % (target, argv[0])
	safe_eval(source, cmd, c)

def unban(c, source, target, argv):
	"""unbans somebody from the current channel"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'unban' requires a parameter (mask)" % source)
		return
	cmd = 'c.mode("%s", "-b %s")' % (target, argv[0])
	safe_eval(source, cmd, c)

def topic(c, source, target, argv):
	"""change the topic of a channel"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'topic' requires a parameter (new topic)" % source)
		return
	cmd = 'c.topic("%s", "%s")' % (target, " ".join(argv).replace('"', r'\"'))
	safe_eval(source, cmd, c)

def myeval(c, source, target, argv):
	"""evaluates an expression"""
	safe_eval(source, " ".join(argv), c)

def myreload(c, source, target, argv):
	"""reloads the event handlers"""
	safe_eval(source, 'self.reload()', c)

def integrate(c, source, target, argv):
	"""integrates a math expression. example: (cos(x))^2"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'integrate' requires a parameter (expression)" % source)
		return
	c.privmsg(target, "http://integrals.wolfram.com/index.jsp?%s" % urllib.urlencode({'expr':argv[0]}))

def bugs(c, source, target, argv):
	from xml.sax.saxutils import unescape
	sock = urllib.urlopen("http://bugs.frugalware.org/getinfo/%s" % argv[0][1:])
	doc = minidom.parseString(sock.read())
	sock.close()
	try:
		id = doc.getElementsByTagName("id")[0].firstChild.toxml()
		title = unescape(': '.join(doc.getElementsByTagName("title")[0].firstChild.toxml().split(': ')[1:]),
			{"&quot;": '"'})
	except IndexError:
		c.privmsg(target, "no such bug")
		return
	type = doc.getElementsByTagName("type")[0].firstChild.toxml()
	status = doc.getElementsByTagName("status")[0].firstChild.toxml()
	opener = "Opened by %s" % doc.getElementsByTagName("opener")[0].firstChild.toxml()
	omail = doc.getElementsByTagName("omail")[0].firstChild.toxml()
	odate = doc.getElementsByTagName("odate")[0].firstChild.toxml()
	link = doc.getElementsByTagName("link")[0].firstChild.toxml().replace('task/', '')
	try:
		aname = " (Assigned to %s)" % doc.getElementsByTagName("aname")[0].firstChild.toxml()
	except IndexError:
		aname = ""
	c.privmsg(target, "14#%s7 %s3 %s%s7 %s (%s)3 %s" % (id, type, status, aname, title, opener, link))

def google(c, source, target, data):
	"""searches the web using google"""
	class myurlopener(urllib.FancyURLopener):
		version = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.2) Gecko/20070225 Firefox/2.0.0.2"

	class HTMLParser(SGMLParser):
		def reset(self):
			SGMLParser.reset(self)
			self.intitle = False
			self.indesc = False
			self.titles = []
			self.title = []
			self.descs = []
			self.desc = []
			self.links = []
			self.link = None

		def start_a(self, attrs):
			for k, v in attrs:
				if k == "class" and v == "l":
					self.intitle = True
					self.links.append(self.link)
				elif k == "href":
					self.link = v

		def start_ul(self, attrs):
			for k, v in attrs:
				if k == "type" and v == "disc":
					self.intitle = True

		def end_a(self):
			if self.intitle:
				self.titles.append("".join(self.title))
				self.title = []
				self.intitle = False

		def start_h2(self, attrs):
			for k, v in attrs:
				if k == "class" and v == "r":
					self.intitle = True

		def end_h2(self):
			if self.intitle:
				self.titles.append("".join(self.title))
				self.title = []
				self.intitle = False
				self.descs.append(None)
				self.links.append(None)

		def start_div(self, attrs):
			for k, v in attrs:
				if k == "class" and v == "s":
					self.indesc = True

		def start_br(self, attrs):
			if self.indesc:
				self.descs.append("".join(self.desc))
				self.desc = []
				self.indesc = False
			elif self.intitle:
				s = "".join(self.title)
				if s[-3:] == "...":
					s = s[:-4]
				self.titles.append(s)
				self.title = []
				self.intitle = False
				self.descs.append(None)
				self.links.append(None)

		def handle_data(self, text):
			if self.intitle:
				self.title.append(text)
			elif self.indesc:
				self.desc.append(text)

	if len(data) < 1:
		c.privmsg(target, "%s: 'google' requires a parameter (search term)" % source)
		return
	elif " ".join(data) == "ryuo's little secret":
		c.privmsg(target, "pwned!")
		return
	urllib._urlopener = myurlopener()
	sock = urllib.urlopen("http://www.google.com/search?" + urllib.urlencode({'q':" ".join(data)}))
	page = sock.read()
	sock.close()

	parser = HTMLParser()
	parser.reset()
	parser.feed(page)
	parser.close()

	if len(parser.titles):
		c.privmsg(target, parser.titles[0].strip())
	else:
		c.privmsg(target, "your search did not match any documents")
	if len(parser.descs) and parser.descs[0]:
		c.privmsg(target, parser.descs[0])
	if len(parser.links) and parser.links[0]:
		c.privmsg(target, parser.links[0])

def tv(c, source, target, data):
	"""spams the channel with television info"""
	class myurlopener(urllib.FancyURLopener):
		version = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.2) Gecko/20070225 Firefox/2.0.0.2"

	class ChanListParser(SGMLParser):
		def reset(self):
			SGMLParser.reset(self)
			self.channels = {}
			self.lastchan = None
			self.intable = False
			self.inspan = False
			self.span = []

		def start_table(self, attrs):
			for k, v in attrs:
				if k == "id" and v == "ctl00_C_G":
					self.intable = True

		def end_table(self):
			self.intable = False

		def start_img(self, attrs):
			if self.intable:
				for k, v in attrs:
					if k == "src":
						self.lastchan = v.split('/')[-1].split('.')[0]

		def start_span(self, attrs):
			if self.intable:
				self.inspan = True

		def end_span(self):
			if self.intable:
				self.inspan = False
				if self.lastchan:
					self.channels["".join(self.span).lower()] = self.lastchan
					self.span = []
					self.lastchan = None

		def handle_data(self, text):
			if self.inspan:
				self.span.append(text)

	if len(data) < 1:
		c.privmsg(target, "%s: 'tv' requires at least one parameter (channel name)" % source)
		return
	url = "http://tv.animare.hu/rss.aspx"
	url2 = "http://tv.animare.hu/rssfeed.aspx?tartalom=aktualistvmusor&tvcsatorna="
	urllib._urlopener = myurlopener()
	sock = urllib.urlopen(url)
	page = sock.read()
	sock.close()

	clp = ChanListParser()
	clp.reset()
	clp.feed(page)
	clp.close()

	channel = " ".join(data)
	if channel.lower() not in clp.channels.keys():
		c.privmsg(target, "no such channel. see %s for available channels" % url)
		return
	id = clp.channels[channel.lower()]
	try:
		sock = urllib.urlopen(url2 + id)
	except IOError, s:
		c.privmsg(target, "problem: %s" % s)
		return
	buf = sock.read()
	try:
		doc = minidom.parseString(buf)
	except Exception, s:
		c.privmsg(target, "problem: %s; %s" % (s, url))
		return
	for i in doc.getElementsByTagName("item"):
		c.notice(source, i.getElementsByTagName("title")[0].firstChild.toxml().replace("\n", ""))

def isbn(c, source, target, data):
	"""searches for isbn numbers using google"""
	class myurlopener(urllib.FancyURLopener):
		version = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.2) Gecko/20070225 Firefox/2.0.0.2"

	class HTMLParser(SGMLParser):
		def reset(self):
			SGMLParser.reset(self)
			self.intitle = False
			self.title = []
			self.indesc = False
			self.desc = []
			self.link = None

		def start_a(self, attrs):
			if self.intitle:
				for k, v in attrs:
					if k == "href":
						self.link = v.replace('&cd=1', '')

		def end_a(self):
			if self.intitle:
				self.title = ["".join(self.title)]
				self.intitle = False

		def end_span(self):
			if self.indesc:
				self.desc = ["by " + "".join(self.desc)]
				self.indesc = False

		def start_div(self, attrs):
			for k, v in attrs:
				if k == "class" and v == "resbdy":
					self.intitle = True

		def start_span(self, attrs):
			for k, v in attrs:
				if k == "class" and v == "ln2":
					self.indesc = True

		def handle_data(self, text):
			if self.intitle:
				self.title.append(text)
			elif self.indesc:
				self.desc.append(text)

	if len(data) < 1:
		c.privmsg(target, "%s: 'isbn' requires a parameter (search term)" % source)
		return
	urllib._urlopener = myurlopener()
	sock = urllib.urlopen("http://books.google.com/books?" + urllib.urlencode({'as_isbn':" ".join(data)}))
	page = sock.read()
	sock.close()

	parser = HTMLParser()
	parser.reset()
	parser.feed(page)
	parser.close()

	if len(parser.title):
		# :-3 becase the end contains some unnecessary utf8 crap
		c.privmsg(target, parser.title[0][:-3])
	else:
		c.privmsg(target, "your search did not match any documents")
	if len(parser.desc):
		c.privmsg(target, parser.desc[0])
	if parser.link:
		c.privmsg(target, parser.link)

def fight(c, source, target, data):
	"""compares the popularity of two words using googlefight"""
	class myurlopener(urllib.FancyURLopener):
		version = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.2) Gecko/20070225 Firefox/2.0.0.2"

	class HTMLParser(SGMLParser):
		def reset(self):
			SGMLParser.reset(self)
			self.inabout = False
			self.resnum = 0

		def handle_data(self, text):
			if text == " of about ":
				self.inabout = True
			elif self.inabout:
				self.resnum = int(text.replace(',', ''))
				self.inabout = False

	if len(data) < 2:
		c.privmsg(target, "%s: 'fight' requires two parameters" % source)
		return
	urllib._urlopener = myurlopener()
	res = []
	for i in data:
		sock = urllib.urlopen("http://www.google.com/search?hl=en&q=%s" % i)
		page = sock.read()
		sock.close()

		parser = HTMLParser()
		parser.reset()
		parser.feed(page)
		parser.close()
		res.append(parser.resnum)

	if res[0] > res[1]:
		win = data[0]
	else:
		win = data[1]
	c.privmsg(target, "googlefight: %s wins! %s vs %s" % (win, res[0], res[1]))

def lc(c, source, target, data):
	"""porget egyet a lamerszamlalon"""
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

def help(c, source, target, argv):
	"""prints this help message"""
	if len(argv) < 1:
		cmds = config.commands.keys()
		cmds.sort()
		c.privmsg(target, "%s: %d available commands: %s" % (source, len(cmds), ", ".join(cmds)))
	else:
		try:
			c.privmsg(target, "%s: %s" % (source, config.commands[argv[0]].__doc__))
		except KeyError:
			c.privmsg(target, "%s: no such command" % source)

def uptime(c, source, target, argv):
	"""tells you the amount of time the bot is available"""
	sock = open("/proc/stat")
	buf = sock.readlines()
	sock.close()
	for i in buf:
		if i.startswith("btime "):
			btime = int(i.split(' ')[1].strip())

	sock = open("/proc/%s/stat" % os.getpid())
	buf = sock.read()
	sock.close()
	ptime = btime+int(buf.split(' ')[21])/100

	diff = time.time()-ptime

	min = 60
	hour = min * 60
	day = hour * 24

	days = int(diff / day)
	hours = int((diff % day) / hour)
	minutes = int((diff % hour) / min)
	seconds = int(diff % min)
	c.privmsg(target, "%s uptime: %dd %dh %dm %ds" % (c.get_nickname(), days, hours, minutes, seconds))

def db(c, source, target, argv):
	"""gets a record from the database. if a second optional parameter is given, then it'll be sent as a notice to the specified nick"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'db' requires a parameter" % source)
		return
	if argv[0] in config.database.keys():
		record = config.database[argv[0]]
		if type(record) == list:
			record = random.choice(record)
		if "\n" in record or " " not in record:
			for i in record.split("\n"):
				c.privmsg(target, "%s" % i)
		else:
			if len(argv) > 1:
				c.notice(argv[1], "%s => %s" % (argv[0], config.database[argv[0]]))
			else:
				c.privmsg(target, "%s: %s => %s" % (source, argv[0], config.database[argv[0]]))
		return True
	else:
		return False

def db_search(c, source, target, argv):
	"""searches the database. if no parameter given then all records will be listed. regexs supported"""
	ret = []
	if len(argv):
		pattern = argv[0]
	else:
		pattern = "."
	for k, v in config.database.items():
		if re.search(pattern, k) or re.search(pattern, v):
			ret.append(k)
	if len(ret):
		ret.sort()
		c.privmsg(target, "%s: the following records match: %s" % (source, ", ".join(ret)))
	else:
		c.privmsg(target, "%s: no matching records" % source)

def darcs(c, source, target, argv):
	"""gives you a deepcmdline to get a given repo"""
	repodir = "/pub/other/homepage-ng/darcs/repos"
	if len(argv) < 1:
		for root, dirs, files in os.walk(repodir):
			repos = dirs
		repos.sort()
		c.privmsg(target, "%s: the following darcs repos are available: %s. use 'darcs foo' to get a deepcmdline" % (source, ", ".join(repos)))
		return
	repo = argv[0]
	found = False
	for root, dirs, files in os.walk(repodir):
		for dir in dirs:
			if dir == repo:
				found = True
	if not found:
		c.privmsg(target, "%s: no such repo" % source)
		return
	else:
		path = os.path.abspath(os.path.join(repodir, os.readlink(os.path.join(repodir, repo))))
		if repo.startswith("frugalware-"):
			local = repo[len("frugalware-"):]
		else:
			local = ""
		c.privmsg(target, "%s: darcs get --partial %s@darcs.frugalware.org:%s %s" % (source, source, path, local))

def git(c, source, target, argv, anon=False, ret=False):
	"""gives you a deepcmdline to clone a given repo. use 'git foo' to get a deepcmdline. use 'git info foo' to get info about a repo"""
	repodir = "/pub/other/homepage-ng/git/repos"
	if len(argv) < 1:
		for root, dirs, files in os.walk(repodir):
			repos = dirs
		repos.sort()
		c.privmsg(target, "%s: the following git repos are available: %s. see 'help git' for more info" % (source, ", ".join(repos)))
		return
	elif len(argv) < 2:
		repo = argv[0]
		found = False
		path = None
		for root, dirs, files in os.walk(repodir):
			for dir in dirs:
				if dir == repo:
					found = True
		if not found:
			matches = glob.glob("/pub/other/people/*/%s" % repo)
			if len(matches):
				found = True
				path = matches[0]
		if not found:
			c.privmsg(target, "%s: no such repo" % source)
			return
		else:
			if not path:
				path = os.path.abspath(os.path.join(repodir, os.readlink(os.path.join(repodir, repo))))
			if repo.startswith("frugalware-"):
				local = repo[len("frugalware-"):]
			else:
				local = ""
			if not anon:
				c.privmsg(target, "%s: git clone %s@git.frugalware.org:%s %s" % (source, source, path, local))
			else:
				if not ret:
					c.privmsg(target, "%s: git clone git://git.frugalware.org%s %s" % (source, path, local))
				else:
					return "%s: git clone git://git.frugalware.org%s %s" % (source, path, local)
	else:
		cmd = None
		cmds = ['info']
		if argv[0] in cmds:
			cmd = argv[0]
			repo = argv[1]
		else:
			repo = argv[0]
			hash = argv[1]
		found = False
		for root, dirs, files in os.walk(repodir):
			for dir in dirs:
				if dir == repo:
					found = True
		if not found:
			c.privmsg(target, "%s: no such repo" % source)
			return
		else:
			if cmd == "info":
				sock = open("%s/%s/.git/description" % (repodir, repo))
				desc = sock.read().strip()
				sock.close()
				sock = open("%s/%s/.git/owner" % (repodir, repo))
				owner = sock.read().strip()
				sock.close()
				c.privmsg(target, "%s: desc: '%s', owner: '%s'" % (source, desc, owner))
			else:
				c.privmsg(target, "%s: http://git.frugalware.org/gitweb/gitweb.cgi?p=%s.git;a=commitdiff;h=%s" % (source, argv[0], argv[1]))

def anongit(c, source, target, argv):
	"""gives you a deepcmdline to clone a given repo anonymously"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'anongit' requires a parameter. use the 'git' command to list available repos" % source)
		return
	git(c, source, target, argv, True)

def repo(c, source, target, argv):
	"""gives you config lines to add a given repo to pacman-g2 config"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'repo' requires a parameter" % source)
		return
	ret = git(c, source, target, argv, anon=True, ret=True).strip().split(': ')[1]
	repo = ret.split('/')[-1]
	c.privmsg(target, "[%s]" % repo)
	c.privmsg(target, "".join([ret.replace('git clone git://git', 'Server = http://ftp'), "/frugalware-i686"]))

def unicode_unescape(match):
	return match.group().decode('unicode_escape')

def dict(c, source, target, argv):
	"""dictionary using dict.sztaki.hu. supported dicts: en,de,fr,it,nl,pl <-> hu. syntax: dict <from>2<to> <word>. example: dict en2hu table (the '2hu' suffix is autocompleted if necessary)"""
	def ret_err(target, reason):
		if target == "#debian.hu":
			c.privmsg(target, "%s, Te itt nem szotarazol bazmeg!!!" % source)
		else:
			c.privmsg(target, "problem: %s" % reason)
		return False
	if len(argv) < 2:
		c.privmsg(target, "%s: 'dict' requires two parameters" % source)
		return
	lang = argv[0]
	word = " ".join(argv[1:])
	try:
		ret = sztakidict.helper(lang, word)
	except IOError:
		ret_err(target, "IOError")
		return
	if ret == "%s: " % word:
		return ret_err(target, "not found")
	c.privmsg(target, ret)

def imdb(c, source, target, data):
	"""searches movies using imdb"""
	class SHTMLParser(SGMLParser):
		def reset(self):
			SGMLParser.reset(self)
			self.link = None

		def start_a(self, attrs):
			for k, v in attrs:
				if k == "href" and v.startswith("/title/"):
					if not self.link:
						self.link = "http://www.imdb.com%s" % v

	class FHTMLParser(SGMLParser):
		def reset(self):
			SGMLParser.reset(self)
			self.ingenre = False
			self.inruntime = False
			self.inplot = False
			self.invote = False
			self.intitle = False
			self.genre = []
			self.runtime = None
			self.plot = None
			self.vote = []
			self.title = []

		def start_title(self, attrs):
			self.intitle = True
		def end_title(self):
			self.title = "".join(self.title)
			self.intitle = False

		def handle_data(self, text):
			if self.ingenre:
				if text == "more":
					self.genre = "genre: " + "".join(self.genre).strip().replace('|', '/')
					self.ingenre = False
				elif text != "\n":
					self.genre.append(text)
			elif self.inruntime:
				self.runtime = "runtime: " + text.strip().replace('|', '/').replace('  ', ' ')
				if self.runtime != "runtime: ":
					self.inruntime = False
			elif self.inplot:
				self.plot = text.strip()
				if len(self.plot):
					self.inplot = False
			elif self.invote:
				if "/" in text:
					self.vote = "score: %s" % text.split("/")[0]
				elif text[-5:] == "votes":
					self.vote += re.sub(r"(.*) votes", r"/\1", text)
					self.invote = False
				elif text == "(awaiting 5 votes)":
					self.vote = None
					self.invote = False
			elif self.intitle:
				self.title.append(text.strip())
			if text == "Genre:":
				self.ingenre = True
			elif text == "Runtime:":
				self.inruntime = True
			elif text == "Plot:":
				self.inplot = True
			elif text == "User Rating:":
				self.invote = True

	class myurlopener(urllib.FancyURLopener):
		version = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.2) Gecko/20070225 Firefox/2.0.0.2"
	urllib._urlopener = myurlopener()
	if len(data) < 1:
		c.privmsg(target, "%s: 'imdb' requires a parameter (search term)" % source)
		return
	try:
		int(data[0])
		id = data[0]
	except ValueError:
		id = None
	if not id:
		sock = sock = urllib.urlopen("http://www.imdb.com/find?" + urllib.urlencode({'s':'all', 'q':" ".join(data)}))
		page = sock.read()
		sock.close()
		parser = SHTMLParser()
		parser.reset()
		parser.feed(page)
		parser.close()
		link = parser.link
	else:
		link = "http://www.imdb.com/title/tt%s/" % id
	try:
		sock = urllib.urlopen(link)
	except AttributeError:
		c.privmsg(target, "no matches")
		return
	page = sock.read()
	sock.close()
	parser = FHTMLParser()
	parser.reset()
	parser.feed(page)
	parser.close()
	if parser.title.startswith("IMDb:"):
		c.privmsg(target, "no matches")
		return
	else:
		try:
			c.privmsg(target, " || ".join(filter((lambda x: x is not None), [parser.title, parser.genre, parser.vote, parser.plot, parser.runtime, link])))
		except TypeError:
			c.privmsg(target, "malformed query")

def wipstatus(c, source, target, argv):
	"""compares the amount of fpms in a wip repo, compared to current. example: 'wipstatus krix/gnome22 x86_64 gnome gnome-extra'"""
	if len(argv)<3:
		c.privmsg(target, "%s: too few params, see help" % source)
		return
	old = os.getcwd()
	os.chdir("/pub/other/people")
	repo = argv[0]
	arch = argv[1]
	pkglist = []
	for i in argv[2:]:
		pkglist += glob.glob("%s/source/%s/*" % (repo, i))
	percent = int(float(len(glob.glob("%s/frugalware-%s/*" % (repo, arch))))/len(pkglist)*100)
	c.privmsg(target, "%s: %s: %d%% completed" % (source, repo, percent))
	os.chdir(old)

def parsedate(c, source, target, argv):
	"""parses a date. it can be handy before using the notify command"""
	if not len(argv):
		c.privmsg(target, "%s: parsedate requires at least one parameter" % source)
		return
	try:
		bad, t, = anydatetime.anydatetime(" ".join(argv))
	except KeyError:
		c.privmsg(target, "%s: can't parse %s as a date string" % (source, ", ".join(argv)))
	if bad:
		c.privmsg(target, "%s: unparsable date items: %s" % (source, ", ".join(bad)))
		return
	c.privmsg(target, "%s: i think this means exactly '%s'" % (source, time.strftime(anydatetime.ISO_DATETIME_FORMAT, t)))

def notify(c, source, target, argv):
	"""notifies somebody about something at a given time in the future"""
	if len(argv) < 4:
		c.privmsg(target, "%s: 'notify' usage: 'notify <nick> <date> about <text>'" % source)
		c.privmsg(target, "%s: example: 'notify janny tomorrow about you need to buy beer'" % source)
		return
	params = " ".join(argv)
	nick = params.split(' about ')[0].split(' ')[0]
	when = " ".join(params.split(' about ')[0].split(' ')[1:])
	text = ' about '.join(params.split(' about ')[1:])
	bad, t = anydatetime.anydatetime(when)
	if bad:
		c.privmsg(target, "%s: unparsable date items: %s" % (source, ", ".join(bad)))
		return
	c.privmsg(target, "%s: ok, i'll notify %s about '%s' @ '%s'" % (source, nick, text, time.strftime(anydatetime.ISO_DATETIME_FORMAT, t)))
	if not hasattr(config, "notifythread") or not config.notifythread.isAlive():
		config.notifythread = NotifyThread(c)
		config.notifythread.start()
		config.notifythread.todo = [(nick, t, text, target, source)]
	else:
		config.notifythread.todo.append((nick, t, text, target, source))

def mojodb(c, source, target, argv):
	"""mirror of Mojojojo's database. one parameter needed. valid subcommands: h[elp]|s[earch]. they require a parameter, too"""
	if len(argv) < 1:
		c.privmsg(target, "%s: 'mojodb' requires a parameter (record name)" % source)
		return
	sock = open("mojodb")
	records = pickle.load(sock)
	sock.close()
	if len(argv) == 1:
		key = argv[0]
		if key in records.keys():
			c.privmsg(target, "%s: %s => %s" % (source, key, records[key]))
		else:
			for k, v in records.items():
				if re.search("^" + key.replace("-", ".*-"), k):
					c.privmsg(target, "%s: %s => %s" % (source, k, v))
					return
			c.privmsg(target, "%s: no such key" % source)
		return
	elif len(argv) == 2:
		if argv[0][0] == 's':
			ret = []
			for k, v in records.items():
				if re.search(argv[1], k) or re.search(argv[1], v):
					ret.append(k)
			if len(ret):
				c.privmsg(target, "%s: mojodb search results: %s" % (source, ", ".join(ret)))
			else:
				c.privmsg(target, "%s: no mojodb search results" % source)
		else:
			c.privmsg(target, "%s: '%s' is not a valid mojodb subcommand" % (source, argv[0]))

def fortune(c, e, source, file, prefix):
	sock = open(file)
	lines = "".join(sock.readlines()).split("\000\n")
	sock.close()
	c.privmsg(e.target(), "%s %s" % (prefix, random.choice(lines).replace("\n", ' ').strip()))

def define(c, source, target, argv):
	"Defines a term using Google."
	if not len(argv):
		c.privmsg(target, "%s: defines requires a parameter" % source)
		return
	google(c, source, target, ["define:"+argv[0]] + argv[1:])

def mid(c, source, target, argv):
	"Searches articles with a given Message-ID on GMane."
	if not len(argv):
		c.privmsg(target, "%s: mid requires at least one parameter" % source)
		return
	opener = urllib2.build_opener()
	sock = opener.open("http://mid.gmane.org/%s" % argv[0])
	if sock.url.startswith("http://mid"):
		c.privmsg(target, "%s: mid '%s' not found" % (source, argv[0]))
	else:
		c.privmsg(target, "%s: %s" % (source, sock.url))

def bullshit(c, source, target, argv):
	"""Web Economy Bullshit Generator (example: 'optimize next-generation e-business')"""
	list1 = ["implement", "utilize", "integrate", "streamline",
			"optimize", "evolve", "transform", "embrace",
			"enable", "orchestrate", "leverage", "reinvent",
			"aggregate", "architect", "enhance",
			"incentivize", "morph", "empower",
			"envisioneer", "monetize", "harness",
			"facilitate", "seize", "disintermediate",
			"synergize", "strategize", "deploy", "brand",
			"grow", "target", "syndicate", "synthesize",
			"deliver", "mesh", "incubate", "engage",
			"maximize", "benchmark", "expedite",
			"reintermediate", "whiteboard", "visualize",
			"repurpose", "innovate", "scale", "unleash",
			"drive", "extend", "engineer", "revolutionize",
			"generate", "exploit", "transition", "e-enable",
			"iterate", "cultivate", "matrix", "productize",
			"redefine", "recontextualize"]
	list2 = ["clicks-and-mortar", "value-added", "vertical",
			"proactive", "robust", "revolutionary",
			"scalable", "leading-edge", "innovative",
			"intuitive", "strategic", "e-business",
			"mission-critical", "sticky", "one-to-one",
			"24/7", "end-to-end", "global", "B2B", "B2C",
			"granular", "frictionless", "virtual", "viral",
			"dynamic", "24/365", "best-of-breed", "killer",
			"magnetic", "bleeding-edge", "web-enabled",
			"interactive", "dot-com", "sexy", "back-end",
			"real-time", "efficient", "front-end",
			"distributed", "seamless", "extensible",
			"turn-key", "world-class", "open-source",
			"cross-platform", "cross-media", "synergistic",
			"bricks-and-clicks", "out-of-the-box",
			"enterprise", "integrated", "impactful",
			"wireless", "transparent", "next-generation",
			"cutting-edge", "user-centric", "visionary",
			"customized", "ubiquitous", "plug-and-play",
			"collaborative", "compelling", "holistic",
			"rich"]
	list3 = ["synergies", "web-readiness", "paradigms", "markets",
			"partnerships", "infrastructures", "platforms",
			"initiatives", "channels", "eyeballs",
			"communities", "ROI", "solutions", "e-tailers",
			"e-services", "action-items", "portals",
			"niches", "technologies", "content", "vortals",
			"supply-chains", "convergence", "relationships",
			"architectures", "interfaces", "e-markets",
			"e-commerce", "systems", "bandwidth",
			"infomediaries", "models", "mindshare",
			"deliverables", "users", "schemas", "networks",
			"applications", "metrics", "e-business",
			"functionalities", "experiences", "web services",
			"methodologies"]
	lists = [list1, list2, list3]
	c.privmsg(target, "Web Economy Bullshit Generator: %s" % " ".join(map(random.choice, lists)))

def bullshit2(c, source, target, argv):
	"""Web 2.0 Bullshit Generator (example: 'create podcasting communities')"""
	list1 = ["aggregate", "beta-test", "integrate", "capture",
			"create", "design", "disintermediate", "enable",
			"integrate", "post", "remix", "reinvent",
			"share", "syndicate", "tag", "incentivize",
			"engage", "reinvent", "harness", "integrate"]
	list2 = ["AJAX-enabled", "A-list", "authentic", "citizen-media",
			"Cluetrain", "data-driven", "dynamic",
			"embedded", "long-tail", "peer-to-peer",
			"podcasting", "rss-capable", "semantic",
			"social", "standards-compliant", "user-centred",
			"user-contributed", "viral", "blogging",
			"rich-client"]
	list3 = ["APIs", "blogospheres", "communities", "ecologies",
			"feeds", "folksonomies", "life-hacks",
			"mashups", "network effects", "networking",
			"platforms", "podcasts", "value",
			"web services", "weblogs", "widgets", "wikis",
			"synergies", "ad delivery", "tagclouds"]
	lists = [list1, list2, list3]
	c.privmsg(target, "Web 2.0 Bullshit Generator: %s" % " ".join(map(random.choice, lists)))

def m8r(c, source, target, argv):
	"""Returns the maintainer of a pckage"""
	if not len(argv):
		c.privmsg(target, "%s: m8r requires a parameter" % source)
		return
	ret = ""
	pkgname = argv[0]
	dirs = glob.glob(os.path.split(config.authors)[0] + "/../../source/*/" + pkgname)
	if not len(dirs):
		c.privmsg(target, "%s: no such package, do you want to package it today?!" % source)
		return
	dir = dirs[0]
	socket = open("%s/FrugalBuild" % dir)
	while True:
		line = socket.readline()
		if not line:
			break
		if line[:14] != "# Maintainer: ":
			continue
		# FIXME: we here hardcore the encoding of the FBs
		ret = line[14:].strip().decode('latin1')
		break
	socket.close()
	c.privmsg(target, ret)

class config:
	server = "irc.freenode.net"
	port = 6667
	nick  = "mxw_"
	password = password.password
	realname = "yeah"
	channels = ['#frugalware', '#frugalware.dev', '#frugalware.hu', '#frugalware.fr', '#frugalware.es', '#debian.hu']
	authors = "/pub/frugalware/frugalware-current/docs/xml/authors.xml"
	logpath = "/pub/other/irclogs"
	# for reporting bugs
	owner = "vmiklos"

	feeds = [Rss("http://frugalware.org/rss/blogs", ["#frugalware", "#frugalware.fr"], "blogs"),
			Rss("http://frugalware.org/rss/bugs", ["#frugalware.dev"], "bugs")]
	duped_feeds = "feeds"
	database = {
			":)": ":D",
			":D": "lol",
			"lol": "what's so funny, dude?",
			"re": "stfu",
			"ping": "pong",
			"bugs": "here we can help, but if you want a bug/feature to be fixed/implemented, then please file a bugreport/feature request at http://bugs.frugalware.org",
			"rtfm": "if you're new to Frugalware, then before asking please read our documentation at http://frugalware.org/docs/, probably your question is answered there",
			"flame": "Frugalware is best! All other distros suck! Oh, sure, we plan to take over the world any minute now ;)",
			"dance": ["0-<\n0-/\n0-\\", " o      o     o    o     o    <o     <o>    o>    o \n.|.    \\|.   \\|/   //    X     \\      |    <|    <|>\n /\\     >\\   /<    >\\   /<     >\\    /<     >\\   /<"],
			"kde4": "http://frugalware.org/~crazy/other/kde4/ <- here you can reach some shots/videos from the upcoming KDE4 for Frugalware. at the moment uploading snapshot fpms would be just a waste of bandwidth, so please don't request them, we'll make them available when it worth to do so. thanks",
			"paste": "if you have a few lines of an error message to others in the channel, please use our Pastebin: http://frugalware.org/paste/. this is because 1) IRC is slow and 2) it breaks other conversations. thanks",
			"persze": "http://www.kancso.hu/zenek/repeta050906.mp3",
			"branches": "Frugalware has two branches. -current is about new features and new functionality is pushed there daily. -stable has major updates twice a year with an upgrade howto and between the major updates there are only security-, bug- and documentations fixes.",
			"ty": "np",
			"rebase": "git config branch.master.rebase true",
			"pic": "http://ftp.frugalware.org/pub/other/people/vmiklos/mxw/mxw.jpg"
			}
	commands = {
			# operator commands
			"opme": opme,
			"op": op,
			"deop": deop,
			"voiceme": voiceme,
			"devoiceme": devoiceme,
			"voice": voice,
			"devoice": devoice,
			"kick": kick,
			"ban": ban,
			"unban": unban,
			"topic": topic,
			# web services
			"google": google,
			"btssearch": (lambda c, source, target, argv: google(c, source, target, ("site:bugs.frugalware.org %s" % " ".join(argv)).split(' '))),
			"fight": fight,
			"lc": lc,
			"define": define,
			# misc
			"help": help,
			"calc": google,
			"eval": myeval,
			"reload": myreload,
			"uptime": uptime,
			"db": db,
			"search": db_search,
			"darcs": darcs,
			"git": git,
			"anongit": anongit,
			"repo": repo,
			"imdb": imdb,
			"mojodb": mojodb,
			"dict": dict,
			"wipstatus": wipstatus,
			"notify": notify,
			"parsedate": parsedate,
			"sms": sms,
			"wtf": wtf,
			"choose": choose,
			"integrate": integrate,
			"isbn": isbn,
			"tv": tv,
			"bullshit": bullshit,
			"bullshit2": bullshit2,
			"mid": mid,
			"m8r": m8r
			}
	triggers = {
			#(lambda e, argv: e.target() == "#frugalware" and " ... " in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: using "..." so much isn't polite to other users. please consider changing that habit.""" % source)),
			(lambda e, argv: e.target().startswith("#frugalware") and "egyenlore" in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: s/egyenlore/egyelore/""" % source)),
			(lambda e, argv: e.target().startswith("#frugalware") and "huje" in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: hulye""" % source)),
			(lambda e, argv: e.target().startswith("#frugalware") and "ijen " in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: ilyen""" % source)),
			(lambda e, argv: e.target().startswith("#frugalware") and "ojan " in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: olyan""" % source)),
			(lambda e, argv: e.target() == "#frugalware.hu" and re.match("^haszn..?l valaki", e.arguments()[0])): (lambda c, e, source, argv: c.privmsg(e.target(), "nem, viccbol van belole csomag")),
			(lambda e, argv: e.arguments()[0].lower() == "yepp!"): (lambda c, e, source, argv: fortune(c, e, source, "akii-fun.lines", "Yepp!")),
			(lambda e, argv: e.arguments()[0].lower() == "argh!" and e.target() not in ["#frugalware", "#frugalware.dev"]): (lambda c, e, source, argv: fortune(c, e, source, "murphy-hu.lines", "Argh!")),
			(lambda e, argv: e.arguments()[0].lower() == "yow!"): (lambda c, e, source, argv: fortune(c, e, source, "yow.lines", "Yow!")),
			(lambda e, argv: re.match("^[0-9.]+[KM]? [a-zA-Z]+ in [a-zA-Z]+$", " ".join(argv[:4])) and len(argv)==4): (lambda c, e, source, argv: google(c, source, e.target(), argv)),
			(lambda e, argv: (not e.target().startswith("#") or e.target() == "#debian.hu") and re.match("^(en|de) [a-zA-Z\xdf\xfc]+$", " ".join(argv))): (lambda c, e, source, argv: dict(c, source, e.target(), argv)),
			(lambda e, argv: re.match("^#[0-9]+$", " ".join(argv))): (lambda c, e, source, argv: bugs(c, source, e.target(), argv))
			}
	highlight_triggers = {
			(lambda e, argv: re.match(r".*\?$", argv[-1]) and e.target() not in ["#frugalware.dev", "#frugalware"]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: persze""" % source)),
			(lambda e, argv: re.match(r"sz..?p.?vagyok\?$", " ".join(argv[-2:])) and e.target() not in ["#frugalware.dev", "#frugalware"]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: nembazdmegolyanvagymintegylapitottbekaazorszaguton!""" % source))
			}
	lastlog = {}

todo = {}

##
# functions used by event handlers
##
def command(self, c, source, target, data):
	class thread (threading.Thread):
		def __init__(self, cmd, argv, c, source, target):
			threading.Thread.__init__(self)
			self.cmd = cmd
			self.argv = argv
			self.c = c
			self.source = source
			self.target = target
		def run (self):
			eval(self.cmd)
	argv = data.split(' ')
	ret = []
	# functions
	if argv[0] in config.commands.keys():
		thread("""config.commands[self.argv[0]](self.c, self.source, self.target, self.argv[1:])""", argv, c, source, target).start()
		return True
	# database commands
	if config.commands['db'](c, source, target, argv):
		return True
	return False

def check_rss(self, c, e):
	current = time.time()
	for i in config.feeds:
		gray = i.title
		i.feed = feedparser.parse(i.url)
		for j in i.feed.entries:
			i.updated = max(time.mktime(j.updated_parsed), i.updated)
			for k in i.targets:
				if time.mktime(j.updated_parsed) > i.updated:
					if i.title == "ping":
						brown = j.author
						green = j.title
					else: # blogs and bugs
						brown = j.title.encode('latin2') # FIXME: hardwired charset
						green = j.link
					c.privmsg(k, "14%s7 %s3 %s" % (gray, brown, green))

def inxml(nick):
	xmldoc = minidom.parse(config.authors)
	for i in xmldoc.getElementsByTagName('author'):
		if unicode(nick.lower()) == i.getElementsByTagName("nick")[0].firstChild.toxml().lower() and i.getElementsByTagName("status")[0].firstChild.toxml() in ["active", "former", "contributor"]:
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

def handle_triggers(e, argv, c, source, highlight=False):
	for k, v in config.triggers.items():
		if k(e, argv):
			v(c, e, source, argv)
			return True
	if highlight:
		for k, v in config.highlight_triggers.items():
			if k(e, argv):
				v(c, e, source, argv)
				return True
	return False

def log(e):
	def makehtml(s):
		# TODO: make html links and colors
		for k, v in {'<':'&lt;', '>':'&gt;'}.items():
			s = s.replace(k, v)
		return s
	if not re.match("#frugalware(|\..{2})$", e.target()):
		return
	nick = e.source().split("!")[0]
	host = e.source().split("!")[1]
	logdir = "%s/%s" % (config.logpath, e.target())
	if not os.path.exists(logdir):
		os.makedirs(logdir)
	datestr = time.strftime("%d-%m-%Y", time.localtime())
	logpath = "%s/%s/%s.html" % (config.logpath, e.target().lower(), datestr)
	if os.path.exists(logpath):
		sock = open(logpath, "a")
	else:
		sock = open(logpath, "w")
		sock.write("""<html><head>
				<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
				<style type="text/css">
				body { font: 8px Verdana, sans-serif; }
				</style>
				<title>%s @ %s</title>
				</head>
				<body>
				<h1 align="center">Log of the %s channel on %s<br>
				<center>%s</center></h1>
				<table width="90%%" align="center">""" % \
					(e.target(), config.server, e.target(), config.server, datestr))
	# group by nick / time
	nickstr = "&lt;%s&gt;" % nick
	timestr = time.strftime("%H:%M", time.localtime())
	if e.target() in config.lastlog.keys():
		prevnick, prevtime = config.lastlog[e.target()]
		if prevnick == nickstr:
			nickstr = ""
		else:
			config.lastlog[e.target()][0] = nickstr
		if prevtime == timestr:
			timestr = ""
		else:
			config.lastlog[e.target()][1] = timestr
	else:
		config.lastlog[e.target()] = [nickstr, timestr]

	# even and odd lines
	if "linenum" in config.lastlog.keys():
		linenum = config.lastlog['linenum']
		linenum += 1
	else:
		linenum = 0
	colors = ['#EEEEEE', '#DDDDDD']
	color = colors[linenum % 2]
	config.lastlog['linenum'] = linenum
	
	if e.eventtype() != "pubmsg":
		config.lastlog[e.target()][0] = ""
	if e.eventtype() == "pubmsg":
		sock.write("""<tr><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td><td bgcolor="%s">%s</td></tr>\n""" % (color, nickstr, color, makehtml(e.arguments()[0]), color, timestr))
	elif e.eventtype() == "ctcp" and e.arguments()[0] == "ACTION":
		sock.write("""<tr><td bgcolor="#FFFFFF" colspan="2"><font size="-1">* %s %s</font></td><td bgcolor="%s">%s</td></tr>\n""" % (nick, makehtml(e.arguments()[1]), color, timestr))
	elif e.eventtype() == "join":
		sock.write("""<tr><td bgcolor="#FFFFFF" colspan="2"><font size="-1">* %s(%s) has joined %s</font></td><td bgcolor="%s">%s</td></tr>\n""" % (nick, host, e.target(), color, timestr))
	elif e.eventtype() == "part":
		sock.write("""<tr><td bgcolor="#FFFFFF" colspan="2"><font size="-1">* %s has left %s (%s)</font></td><td bgcolor="%s">%s</td></tr>\n""" % (nick, e.target(), " ".join(e.arguments()), color, timestr))
	# TODO: quit
	sock.close()

##
# the event handlers
##
def on_nicknameinuse(self, c, e):
	c.nick(config.nick + "_")
	c.privmsg("nickserv", "ghost %s %s" % (config.nick, config.password))
	time.sleep(2)
	c.nick(config.nick)
	c.privmsg("nickserv", "identify %s" % config.password)
	time.sleep(2)

def on_welcome(self, c, e):
	c.privmsg("nickserv", "identify %s" % config.password)
	time.sleep(2)
	for i in config.channels:
		c.join(i)

def on_privmsg(self, c, e):
	nick = e.source().split("!")[0]
	source = e.source().split("!")[0]
	argv = e.arguments()[0].split(" ")
	if command(self, c, nick, nick, e.arguments()[0]):
		return
	# trigger
	# hack. create an event sutable for triggers
	tre = Event(e.eventtype(), e.source(), nick, e.arguments())
	if handle_triggers(tre, argv, c, source, highlight=True):
		return
	c.privmsg(nick, "'%s' is not a valid command" % (argv[0]))

def on_pubmsg(self, c, e):
	highlight = False
	source = e.source().split("!")[0]
	argv = e.arguments()[0].split(" ")
	data = e.arguments()[0][len(c.get_nickname()):]
	if data[:1] == "," or data[:1] == ":":
		data = data[1:]
	# highlight
	if e.arguments()[0].startswith(c.get_nickname()):
		highlight = True
		if command(self, c, source, e.target(), data.strip()):
			return
		# trigger
		# hack. create an event sutable for triggers
		e = Event(e.eventtype(), e.source(), e.target(), [data.strip()])
		argv = e.arguments()[0].split(" ")
		if handle_triggers(e, argv, c, source, highlight=True):
			return
	# trigger
	if handle_triggers(e, argv, c, source):
		return
	if highlight:
		cmdline = " ".join(argv)
		if "mastah" in cmdline:
			c.privmsg(e.target(), "%s: sorry, sir" % source)
		else:
			c.privmsg(e.target(), "%s: '%s' is not a valid command" % (source, argv[0]))
	log(e)

def on_bug(self, c, e):
	type, value, tb = sys.exc_info()
	stype = str(type).split("'")[1]
	print "Traceback (most recent call last):"
	print "".join(traceback.format_tb(tb)).strip()
	print "%s: %s" % (stype, value)

	badline = inspect.trace()[-1]
	c.privmsg(config.owner, "%s at file %s line %d" % (stype, badline[1], badline[2]))

def on_join(self, c, e):
	def hex2ip(s):
		return ".".join(["%d"%int(n, 16) for n in (s[0:2],s[2:4],s[4:6],s[6:8])])
	nick = e.source().split("!")[0]
	if e.target() == "#frugalware.dev":
		cmd = 'c.mode("%s", "+v %s")' % (e.target(), nick)
		safe_eval(nick, cmd, c)
	elif re.match(r".*[0-9a-f]{8}@.*", e.source()):
		try:
			ip = hex2ip(re.sub(r".*([0-9a-f]{8})@.*", r"\1", e.source()))
			try:
				host = socket.gethostbyaddr(ip)[0]
				c.privmsg(e.target(), "%s is from %s (%s)" % (nick, host, ip))
			except socket.error:
				c.privmsg(e.target(), "Could not resolve: %s" % ip)
		except ValueError:
			pass
	log(e)

def on_identified(self, c, e):
	global todo

	nick = e.arguments()[1]
	if nick not in todo.keys():
		return
	for i in todo[nick][-1].split("\n"):
		eval(compile(i, "eval", "single"))
		time.sleep(1)
	if nick in todo.keys():
		del todo[nick]

def on_quit(self, c, e):
	self.rssthread.dieplz = True

def on_pong(self, c, e):
	if not hasattr(self, "rssthread") or not self.rssthread.isAlive():
		self.rssthread = RssThread(self, c, e)
		self.rssthread.start()
	if not hasattr(self, "sockthread") or not self.sockthread.isAlive():
		self.sockthread = SockThread(c)
		self.sockthread.start()

def on_ctcp(self, c, e):
	if e.arguments()[0] == "VERSION":
		sock = os.popen("git describe")
		ver = sock.read().strip()
		sock.close()
		c.ctcp_reply(e.source().split('!')[0], "VERSION mxw %s - running on Frugalware Linux" % ver)
	log(e)

def on_part(self, c, e):
	log(e)
