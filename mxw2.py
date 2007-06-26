#!/usr/bin/env python

from ircbot import SingleServerIRCBot
import events

class Mxw2(SingleServerIRCBot):
	def __init__(self):
		config = events.config
		SingleServerIRCBot.__init__(self, [(config.server, config.port)], config.nick, config.realname)
		self.reload()
	
	def reload(self):
		reload(events)
		self.events = {}
		for i in dir(events):
			if not i.startswith("__"):
				self.events[i] = getattr(events, i)

if __name__ == "__main__":
	mxw2 = Mxw2()
	mxw2.start()
