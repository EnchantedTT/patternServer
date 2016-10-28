from nltk.corpus import cmudict
from pattern.en import parse, parsetree, wordnet, NOUN

def getArticleFeatures(parsedSents, sentences):
	errors = []
	features = []
	headList = []
	count = -1	
	for i in range(len(parsedSents)):
		if parsedSents[i] == None:
			continue
		s = parsedSents[i]
		sHeads = []
		for chunk in s.chunks:
			print chunk

def getCountsFeatures(parsedSents, sentences):
	pass