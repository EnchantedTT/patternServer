from nltk.corpus import cmudict
from pattern.en import parse, parsetree, wordnet, NOUN, singularize, pluralize
import utils
import settings
import logging

LOGGER = logging.getLogger("pattern.server")
#get count features and errors
def getCountsFeatures(parsedSents, sentences):
	errors = []
	features = []
	for i in range(len(parsedSents)):
		if parsedSents[i] == None:
			continue
		s = parsedSents[i]
		sent = sentences[i]
		for chunk in s.chunks:
			if chunk.type == 'NP':
				head = utils.getHeadFeatures(chunk)
				if head == None or head.type == 'PRP':
					continue #ignore PRP and None
				#get celex features
				isPlural = utils.getCount(head)
				c_list = utils.getCelex(head)
				if c_list == None:
					continue
				#apply some precheck rules
				error = utils.precheckCount(c_list, head, sent)
				if error != None:
					e = dict()
					e['start'] = error.start
					e['end'] = error.end
					e['output'] = error.output
					e['desc'] = error.description
					e['type'] = error.type_
					e['original'] = error.original
					e['newSent'] = error.newSent
					errors.append(e)
					continue

				#for the rest of the NP nouns, extract features for  classifier
				article = utils.getOriginalArticle(chunk)
				bef_word, bef_pos, aft_word, aft_pos = utils.getNNFeatures(s, head)
				adj, adj_grade, pdt, prp, relation = utils.getChunkFeatures(chunk)
				wordnet = utils.getWordNet(head)
				output = ''
				if isPlural == 'P':
					output = singularize(head.lemma)
				else:
					output = pluralize(head.lemma)
				
				#features
				feature = []
				feature.append(isPlural)
				feature.append(article)
				feature.append(head.lemma)
				feature.append(wordnet)
				feature.append(adj)
				feature.append(adj_grade)
				feature.append(pdt)
				feature.append(prp)
				feature.append(relation)
				feature.extend(c_list)
				feature.extend(bef_word)
				feature.extend(bef_pos)
				feature.extend(aft_word)
				feature.extend(aft_pos)

				#index of NP chunk, head and article
				index = []
				index.append(i)
				index.append(head.index)
				r = dict()
				r["feature"] = feature
				r["index"] = index
				r["output"] = output
				features.append(r)
	return errors, features

#get article features and errors
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
				#filter NP chunk size bigger than 4
				if len(chunk.words) > 4:
					continue
				head = utils.getHeadFeatures(chunk)
				if head == None or head.type == 'PRP':
					continue #ignore PRP and None

				#get NP article
				article, s_article = utils.getArticle(chunk)
				if s_article == 'O':
					continue #ignore DT which is not a, an or the

				#precheck a/an singular and plural of this NP
				c_list = utils.getCountable(head)
				isUncount = False
				if c_list[0] == 'N' and c_list[1] == 'Y':
					isUncount = True
				error = utils.precheckArticle(article, sent, head, chunk, isUncount)
				if error != None:
					e = dict()
					e['start'] = error.start
					e['end'] = error.end
					e['output'] = error.output
					e['desc'] = error.description
					e['type'] = error.type_
					e['original'] = error.original
					e['newSent'] = error.newSent
					errors.append(e)
					continue

				#for the rest of the NP chunk, extract features for classifier
				bef3pos, aft3pos = utils.getAround(head.index, s, article)
				bnp_word, bnp_pos = utils.getBeforeNP(chunk, s)
				anp_word, anp_pos = utils.getAfterNP(chunk, s)
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