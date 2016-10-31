class Error:
	def __init__(self, start, end, output, description, type_, original=None, newSent=None):
		self.start = start
		self.end = end
		self.output = output
		self.description = description
		self.type_ = type_
		self.original = original
		self.newSent = newSent

	def set_original(self, original):
		self.original = original

	def set_newSent(self, newSent):
		self.newSent = newSent

	def toString(self):
		return self.start, self.end, self.output, self.description, self.type_, str(self.original), self.newSent