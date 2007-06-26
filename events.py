import traceback, inspect, sys
from xml.dom import minidom

class config:
	server = "irc.freenode.net"
	port = 6667
	nick  = "mxw2"
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
	# FIXME: better auth & error handling
	elif argv[0] == "eval" and source == config.owner:
		c.privmsg(target, "%s: eval result: '%s'" % (source, eval(" ".join(argv[1:]))))
	elif argv[0] == ":)":
		c.privmsg(target, "%s: :D" % source)
	elif argv[0] == ":D":
		c.privmsg(target, "%s: lol" % source)
	else:
		c.privmsg(target, "%s: '%s' is not a valid command" % (source, argv[0]))

def inxml(nick):
	xmldoc = minidom.parse(config.authors)
	for i in xmldoc.getElementsByTagName('author'):
		if unicode(nick) == i.getElementsByTagName("nick")[0].firstChild.toxml():
			return True
	return False

##
# the event handlers
##
def on_welcome(self, c, e):
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
	global todo

	nick = e.source().split("!")[0]
	if not inxml(nick):
		return
	cmd = "MODE %s +v %s" % (e.target(), nick)
	if nick in todo.keys():
		todo[nick].append(cmd)
	else:
		todo[nick] = [cmd]
	c.whois([nick])

def on_identified(self, c, e):
	global todo

	nick = e.arguments()[0]
	if nick not in todo.keys():
		return
	c.send_raw(todo[nick][-1])
	del todo[nick]
