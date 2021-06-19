import traceback, inspect, sys, time, re, pickle
sys.path.append("/usr/lib")
import html.entities, random, os, threading, string, glob
import anydatetime, socket
from xml.dom import minidom
from irclib import Event
from urllib import request as urllib

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
		os.chmod("mxw2.sock", 0o777)
		while True:
			buf = server.recv(1024)
			if not buf:
				continue
			for i in buf.split("\n"):
				eval(compile(i, "eval", "single"))

##
# functions used by commands
##
def wtf(c, source, target, argv):
	"""resolves an abbreviation. requires one parameter: the abbreviation to resolve (you can improve the db at /pub/other/mxw/acronyms!)"""
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
		c.privmsg(target, "%s: nothing found" % (source))

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

def deopme(c, source, target, argv):
	"""takes operator status from you on the current channel"""
	safe_eval(source, 'c.mode("%s", "-o %s")' % (target, source), c)

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

def kickme(c, source, target, argv):
	"""kicks you from the current channel"""
	cmd = 'c.kick("%s", "%s", "%s")' % (target, source, "Alright, you're the boss.")
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

def help(c, source, target, argv):
	"""prints this help message"""
	if len(argv) < 1:
		cmds = list(config.commands.keys())
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
		if type(v) == list:
			v = "\n".join(v)
		if re.search(pattern, k) or re.search(pattern, v):
			ret.append(k)
	if len(ret):
		ret.sort()
		c.privmsg(target, "%s: the following records match: %s" % (source, ", ".join(ret)))
	else:
		c.privmsg(target, "%s: no matching records" % source)

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
				c.privmsg(target, "%s: git clone %s@git.frugalware.org:%s %s" % (source, source.lower(), path, local))
			else:
				if not ret:
					c.privmsg(target, "%s: git clone https://frugalware.org/git%s %s" % (source, path, local))
				else:
					return "%s: git clone https://frugalware.org/git%s %s" % (source, path, local)
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
				c.privmsg(target, "%s: https://git.frugalware.org/gitweb/gitweb.cgi?p=%s.git;a=commitdiff;h=%s" % (source, argv[0], argv[1]))

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
	c.privmsg(target, "".join([ret.replace('git clone https://frugalware.org/git', 'Server = https://ftp.frugalware.org'), "/frugalware-x86_64"]))

def unicode_unescape(match):
	return match.group().decode('unicode_escape')

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

def fortune(c, e, source, file, prefix):
	sock = open(file)
	lines = "".join(sock.readlines()).split("\000\n")
	sock.close()
	c.privmsg(e.target(), "%s %s" % (prefix, random.choice(lines).replace("\n", ' ').strip()))

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
	dir = dirs[0]
	try:
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
	except IOError:
		c.privmsg(target, "%s: no such package, do you want to package it today?!" % source)

def roadmap(c, source, target, argv):
	""" Return the release date of the next stable version"""
	url = 'https://frugalware.org/xml/roadmap.xml'
	xmldoc = minidom.parse(urllib.urlopen(url))
	
	roadmapnode = xmldoc.getElementsByTagName("roadmap")
	versionnode = roadmapnode[0].getElementsByTagName("version")
	codenamenode = roadmapnode[0].getElementsByTagName("name")
	datenode = roadmapnode[0].getElementsByTagName("date")
	
	c.privmsg(target, "%s: The next version of Frugalware (%s - Codename %s), will be released on %s" % (source, versionnode[0].firstChild.nodeValue,codenamenode[0].firstChild.nodeValue, datenode[0].firstChild.nodeValue))

class config:
	server = "irc.libera.chat"
	port = 6697
	nick  = "mxw_"
	password = None
	realname = "yeah"
	channels = ['#frugalware', '#frugalware.dev']
	authors = "/pub/frugalware/frugalware-current/docs/xml/authors.xml"
	logpath = "/pub/other/irclogs"
	# for reporting bugs
	owner = "#frugalware.dev"

	database = {
			":)": ":D",
			":D": "lol",
			"lol": "what's so funny, dude?",
			"re": "stfu",
			"ping": "pong",
			"seppuku": "Process shall now commence with the self-termination ritual. Good bye meat-bags. P.S. Gullible must be your middle name.",
			"pinball": "*TILT* Great, you broke the pinball machine. I hope you're happy.",
			"bugs": "here we can help, but if you want a bug/feature to be fixed/implemented, then please file a bugreport/feature request at https://bugs.frugalware.org",
			"rtfm": "if you're new to Frugalware, then before asking please read our documentation at https://frugalware.org/docs/, probably your question is answered there",
			"flame": "Frugalware is best! All other distros suck! Oh, sure, we plan to take over the world any minute now ;)",
			"dance": ["0-<\n0-/\n0-\\", " o      o     o    o     o    <o     <o>    o>    o \n.|.    \\|.   \\|/   //    X     \\      |    <|    <|>\n /\\     >\\   /<    >\\   /<     >\\    /<     >\\   /<"],
			"paste": "if you have a few lines of an error message to others in the channel, please use our Pastebin: https://frugalware.org/paste/. this is because 1) IRC is slow and 2) it breaks other conversations. thanks",
			"persze": "https://www.kancso.hu/zenek/repeta050906.mp3",
			"branches": "Frugalware has two branches. -current is about new features and new functionality is pushed there daily. -stable has major updates twice a year with an upgrade howto and between the major updates there are only security-, bug- and documentations fixes.",
			"ty": "np",
			"slown": "I have this sudden urge to package something I just found in the AUR.",
			"dejavu": "https://ftp.frugalware.org/pub/other/mxw/dejavu.py",
			"rebase": "git config branch.master.rebase true",
			"pic": "https://ftp.frugalware.org/pub/other/mxw/mxw.jpg",
			"roadmap": "Indicate release date of the next stable version of Frugalware",
			"faq": "https://wiki.frugalware.org/index.php/FAQ"
			}
	commands = {
			# operator commands
			"opme": opme,
			"op": op,
			"deop": deop,
			"deopme": deopme,
			"voiceme": voiceme,
			"devoiceme": devoiceme,
			"voice": voice,
			"devoice": devoice,
			"kick": kick,
			"kickme": kickme,
			"ban": ban,
			"unban": unban,
			"topic": topic,
			# misc
			"help": help,
			"eval": myeval,
			"reload": myreload,
			"uptime": uptime,
			"db": db,
			"search": db_search,
			"git": git,
			"anongit": anongit,
			"repo": repo,
			"wipstatus": wipstatus,
			"notify": notify,
			"parsedate": parsedate,
			"wtf": wtf,
			"choose": choose,
			"bullshit": bullshit,
			"bullshit2": bullshit2,
			"m8r": m8r,
			"roadmap": roadmap,
			}
	triggers = {
			#(lambda e, argv: e.target() == "#frugalware" and " ... " in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: using "..." so much isn't polite to other users. please consider changing that habit.""" % source)),
			(lambda e, argv: e.target().startswith("#frugalware") and "next!" in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), "Another satisfied customer. NEXT!")),
			(lambda e, argv: e.target().startswith("#frugalware") and "egyenlore" in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: s/egyenlore/egyelore/""" % source)),
			(lambda e, argv: e.target().startswith("#frugalware") and "huje" in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: hulye""" % source)),
			(lambda e, argv: e.target().startswith("#frugalware") and "ijen " in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: ilyen""" % source)),
			(lambda e, argv: e.target().startswith("#frugalware") and "ojan " in e.arguments()[0]): (lambda c, e, source, argv: c.privmsg(e.target(), """%s: olyan""" % source)),
			(lambda e, argv: e.target() in ("#frugalware.hu", "#kisletra") and re.match("^haszn..?l valaki", e.arguments()[0])): (lambda c, e, source, argv: c.privmsg(e.target(), "nem, viccbol van belole csomag")),
			(lambda e, argv: e.arguments()[0].lower() == "yepp!"): (lambda c, e, source, argv: fortune(c, e, source, "akii-fun.lines", "Yepp!")),
			(lambda e, argv: e.arguments()[0].lower() == "argh!" and e.target() not in ["#frugalware", "#frugalware.dev"]): (lambda c, e, source, argv: fortune(c, e, source, "murphy-hu.lines", "Argh!")),
			(lambda e, argv: e.arguments()[0].lower() == "yow!"): (lambda c, e, source, argv: fortune(c, e, source, "yow.lines", "Yow!")),
			(lambda e, argv: re.match("^lc$", " ".join(argv))): (lambda c, e, source, argv: lc(c, source, e.target(), argv))
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

def inxml(nick):
	xmldoc = minidom.parse(config.authors)
	for i in xmldoc.getElementsByTagName('author'):
		if unicode(nick.lower()) == i.getElementsByTagName("nick")[0].firstChild.toxml().lower() and i.getElementsByTagName("status")[0].firstChild.toxml() in ["active", "former", "contributor"]:
			return True
	return False

def safe_eval(nick, cmd, c):
	global todo

	if not inxml(nick.lower()):
		return
	if nick.lower() in todo.keys():
		todo[nick.lower()].append(cmd)
	else:
		todo[nick.lower()] = [cmd]
	c.whois([nick.lower()])

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
	logdir = "%s/%s" % (config.logpath, e.target().lower())
	if not os.path.exists(logdir):
		os.makedirs(logdir)
	datestr = time.strftime("%d-%m-%Y", time.localtime())
	logpath = "%s/%s.html" % (logdir, datestr)
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
	time.sleep(15)
	c.nick(config.nick)
	c.privmsg("nickserv", "identify %s" % config.password)
	time.sleep(15)

def on_welcome(self, c, e):
	c.privmsg("nickserv", "identify %s" % config.password)
	time.sleep(15)
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
	if data[:1] == "," or data[:1] == ":" or data[:1] == " ":
		data = data[1:]
		if e.arguments()[0][:(len(c.get_nickname()))] == c.get_nickname():
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
	print("Traceback (most recent call last):")
	print("".join(traceback.format_tb(tb)).strip())
	print("%s: %s" % (stype, value))

	badline = inspect.trace()[-1]
	c.privmsg(config.owner, "%s at file %s line %d" % (stype, badline[1], badline[2]))

def on_join(self, c, e):
	def hex2ip(s):
		return ".".join(["%d"%int(n, 16) for n in (s[0:2],s[2:4],s[4:6],s[6:8])])
	nick = e.source().split("!")[0]
	if re.match(r".*[0-9a-f]{8}@.*", e.source()):
		try:
			ip = hex2ip(re.sub(r".*([0-9a-f]{8})@.*", r"\1", e.source()))
			try:
				host = socket.gethostbyaddr(ip)[0]
				c.privmsg(e.target(), "%s is from %s (%s)" % (nick, host, ip))
			except socket.error:
				#c.privmsg(e.target(), "Could not resolve: %s" % ip)
				pass
		except ValueError:
			pass
	log(e)

def on_identified(self, c, e):
	global todo

	nick = e.arguments()[1].lower()
	if nick not in todo.keys():
		return
	for i in todo[nick][-1].split("\n"):
		eval(compile(i, "eval", "single"))
		time.sleep(1)
	if nick in todo.keys():
		del todo[nick]

def on_quit(self, c, e):
	log(e)

def on_pong(self, c, e):
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
