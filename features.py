from nltk.corpus import cmudict
from pattern.en import parse, parsetree, wordnet, NOUN
import utils

def getArticleFeatures(parsedSents, sentences):
	errors = []
	features = []
	headList = []
	for i in range(len(parsedSents)):
		if parsedSents[i] == None:
			continue
		s = parsedSents[i]
		sent = sentences[i]
		sHeads = set()
		for chunk in s.chunks:
			if chunk.type == 'NP':
				head = utils.getHeadFeatures(chunk)
				if chunk.head.type == 'PRP' or head == None:
					continue #ignore PRP and None

				#get NP article
				article, s_article = utils.getArticle(chunk)
				if s_article == 'O':  
					continue #ignore DT which is not a, an or the

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
				isPlural = utils.getCount(head)
				pp, pps = utils.prepModify(chunk)
				adj, adj_grade, pdt, prp, relation = utils.getChunkFeatures(chunk)
				ref = utils.getRef(headList, head, sHeads)
				vowel = utils.isVowel(chunk, article)

				#features
				feature = []
				feature.append(s_article)
				feature.append(head.string)
				feature.append(head.lemma)
				feature.append(head.type)
				feature.append(isPlural)
				feature.append(wordnet)
				feature.append(pp)
				feature.append(pps)
				feature.append(adj)
				feature.append(adj_grade)
				feature.append(pdt)
				feature.append(prp)
				feature.append(relation)
				feature.append(ref)
				feature.append(bnp_word)
				feature.append(bnp_pos)
				feature.append(anp_word)
				feature.append(anp_pos)
				feature.extend(c_list)
				feature.extend(bef3pos)
				feature.extend(aft3pos)

				#index of NP chunk, head and article
				index = []
				index.append(i)
				index.append(chunk.start)
				index.append(chunk.stop)
				index.append(head.index)
				if article == None:
					#if need article where to insert?
					index.append(-1)
				else:
					index.append(article.index)
				index.append(vowel)
				r = dict()
				r["feature"] = feature
				r["index"] = index
				features.append(r)

				sHeads.add(head.string.lower())
		headList.append(sHeads)
		if len(headList) > 5:
			del headList[0]
	return errors, features

def getCountsFeatures(parsedSents, sentences):
	pass