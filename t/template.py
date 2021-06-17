#!/usr/bin/env python3

import sys
sys.path.append("..")
from events import @FUNCTION@

class C:
	def privmsg(self, target, text):
		print("privmsg: %s" % text)
	def notice(self, target, text):
		print("notice: %s" % text)

c = C()

@FUNCTION@(c, "source", "target", sys.argv[1:])
