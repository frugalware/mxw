#!/usr/bin/env python

from ircbot import SingleServerIRCBot
from config import config

class Mxw2(SingleServerIRCBot):
	def __init__(self):
		SingleServerIRCBot.__init__(self, [(config.server, config.port)], config.nick, config.realname)

	def on_welcome(self, c, e):
		for i in config.channels:
			c.join(i)

	def on_privmsg(self, c, e):
		nick = e.source().split("!")[0]
		self.command(c, nick, nick, e.arguments()[0])

	def on_pubmsg(self, c, e):
		# highlight
		if e.arguments()[0].startswith(c.get_nickname()):
			source = e.source().split("!")[0]
			data = e.arguments()[0][len(c.get_nickname()):].strip()
			if data[:1] == "," or data[:1] == ":":
				data = data[1:].strip()
			self.command(c, source, e.target(), data)

	def command(self, c, source, target, data):
		argv = data.split(' ')
		ret = []
		if argv[0] == ":)":
			c.privmsg(target, "%s: :D" % source)
		elif argv[0] == ":D":
			c.privmsg(target, "%s: lol" % source)
		else:
			c.privmsg(target, "%s: '%s' is not a valid command" % (source, cmd))

if __name__ == "__main__":
	mxw2 = Mxw2()
	mxw2.start()
