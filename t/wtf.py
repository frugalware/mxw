#!/usr/bin/env python

import sys
sys.path.append("..")
from events import wtf

class C:
	def privmsg(self, target, text):
		print "privmsg: %s" % text
	def notice(self, target, text):
		print "notice: %s" % text

c = C()

wtf(c, "source", "target", sys.argv[1:])
