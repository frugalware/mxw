import traceback, inspect, sys, password, time, urllib
from xml.dom import minidom
from sgmllib import SGMLParser

class config:
	server = "irc.freenode.net"
	port = 6667
	nick  = "mxw2"
	password = password.password
	realname = "yeah"
	channels = ['#fdb']
	authors = "/home/ftp/pub/frugalware/frugalware-current/docs/xml/authors.xml"
	# for reporting bugs
	owner = "vmiklos"

todo = {}

##
# functions used by event handlers
##
def command(self, c, source, target, data):
	argv = data.split(' ')
	ret = []
	if argv[0] == "reload":
		self.reload()
		c.privmsg(target, "%s: reload done" % source)
	elif argv[0] == "eval":
		safe_eval(source, " ".join(argv[1:]), c)
	# operator commands
	elif argv[0] == "opme":
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
	# end of operator commands
	# web services
	elif argv[0] == "google":
		google(c, source, target, argv[1:])
	# end of web services
	elif argv[0] == ":)":
		c.privmsg(target, "%s: :D" % source)
	elif argv[0] == ":D":
		c.privmsg(target, "%s: lol" % source)
	else:
		c.privmsg(target, "%s: '%s' is not a valid command" % (source, argv[0]))

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
	# highlight
	if e.arguments()[0].startswith(c.get_nickname()):
		source = e.source().split("!")[0]
		data = e.arguments()[0][len(c.get_nickname()):].strip()
		if data[:1] == "," or data[:1] == ":":
			data = data[1:].strip()
		command(self, c, source, e.target(), data)

def on_bug(self, c, e):
	type, value, tb = sys.exc_info()
	stype = str(type).split("'")[1]
	print "Traceback (most recent call last):"
	print "".join(traceback.format_tb(tb)).strip()
	print "%s: %s" % (stype, value)

	badline = inspect.trace()[-1]
	c.privmsg(config.owner, "%s at file %s line %d" % (stype, badline[1], badline[2]))

def on_join(self, c, e):
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
