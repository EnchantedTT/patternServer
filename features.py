from nltk.corpus import cmudict
from pattern.en import parse, parsetree, wordnet, NOUN

def getArticleFeatures(pss, ss):
	errors = []
	features = []
	headList = []
	count = -1	
	for i in range(len(pss)):
		if pss[i] == None:
			continue
		s = pss[i]
		print s
		sHeads = []
		for chunk in s.chunks:
			print chunk