from events import tv

class C:
	def privmsg(self, target, text):
		print text

c = C()

tv(c, "source", "target", ["Discovery Travel"])
