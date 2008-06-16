#!/usr/bin/env python

import sys
sys.path.append("..")
from events import choose

class C:
	def privmsg(self, target, text):
		print "privmsg: %s" % text
	def notice(self, target, text):
		print "notice: %s" % text

c = C()

choose(c, "source", "target", sys.argv[1:])
