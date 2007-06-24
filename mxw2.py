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
		c.privmsg(nick, "hey %s!" % nick)

	def on_pubmsg(self, c, e):
		if e.arguments()[0].startswith(c.get_nickname()):
			c.privmsg(e.target(), "hey %s!" % e.source().split("!")[0])

if __name__ == "__main__":
	mxw2 = Mxw2()
	mxw2.start()
