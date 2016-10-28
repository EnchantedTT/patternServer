class Error:
	def __init__(self, start, end, output, description, type_):
		self.start = start
		self.end = end
		self.output = output
		self.description = description
		self.type_ = type_

	def toString(self):
		return self.start, self.end, self.output, self.description, self.type_