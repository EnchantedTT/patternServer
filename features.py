from nltk.corpus import cmudict
from pattern.en import parse, parsetree, wordnet, NOUN
import utils

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
			if chunk.type == 'NP':
				print utils.getHeadFeatures(chunk)

def getCountsFeatures(parsedSents, sentences):
	pass