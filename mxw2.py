#!/usr/bin/env python3

from ircbot import SingleServerIRCBot
import events, imp

class Mxw2(SingleServerIRCBot):
	def __init__(self):
		config = events.config
		SingleServerIRCBot.__init__(self, [(config.server, config.port)], config.nick, config.realname)
		self.reload()
	
	def reload(self):
		imp.reload(events)
		self.events = {}
		for i in dir(events):
			if not i.startswith("__"):
				self.events[i] = getattr(events, i)

if __name__ == "__main__":
	while True:
		try:
			mxw2 = Mxw2()
			mxw2.start()
		except Exception:
			pass
