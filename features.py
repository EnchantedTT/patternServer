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
		sent = sentences[i]
		sHeads = []
		for chunk in s.chunks:
			if chunk.type == 'NP':
				head = utils.getHeadFeatures(chunk)
				if chunk.head.type == 'PRP' or head == None:
					continue #ignore PRP and None

				#get NP article
				article, s_article = utils.getArticle(chunk)
				if s_article == 'O':  
					continue #ignore DT which is not a, an or the
				print article
				#precheck a/an singular and plural of this NP
				error = utils.precheckArticle(article, sent, head, chunk)
				if error != None:
					e = dict()
					e['start'] = error.start
					e['end'] = error.end
					e['output'] = error.output
					e['desc'] = error.description
					e['original'] = error.original
					e['newSent'] = error.newSent
					errors.append(e)
					continue

				#for the rest of the NP chunk, extract features for classifier
				bef3pos, aft3pos = utils.getAround(head.index, s, article)
				bnp_word, bnp_pos = utils.getBeforeNP(chunk, s)
				anp_word, anp_pos = utils.getAfterNP(chunk, s)
				c_list = utils.getCountable(head)
				wordnet = utils.getWordNet(head)
				pp, pps = utils.prepModify(chunk)
				print pp, pps

def getCountsFeatures(parsedSents, sentences):
	pass