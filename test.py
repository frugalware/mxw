from events import isbn

class C:
	def privmsg(self, target, text):
		print text

c = C()

isbn(c, "source", "target", ["9639429767"])
