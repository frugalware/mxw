from config import config

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
