from nltk.corpus import cmudict
from pattern.en import parse, parsetree, wordnet, NOUN
from BasicModels import Error

PRON = cmudict.dict()
AEIOU = ['A', 'E', 'I', 'O', 'U']

#countabl features from celex
def readNounList(fileName):
	nounList = open(fileName, "r")
	raw = nounList.read().splitlines()
	maps = dict()
	for line in raw:
		data = line.strip().split("\t")
		key = data[0]
		cop = data[1]
		if len(data) != 14:
			print "Read list wrong!"
			sys.exit(0)
		if maps.has_key(key):
			tmp = maps.get(key)
			if cop > tmp:
				maps[key] = data[1:]
			else:
				pass
		else:
			maps[key] = data[1:]
	return maps

NOUNLIST = "static/NounMap.list"
maps = readNounList(NOUNLIST)
NER_VALUE = ['N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'Y', 'N']
NA_VALUE = ['N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N']
def getCountable(head):
	if maps.has_key(head.lemma):
		return maps[head.lemma][2:]
	elif '-' in head.type:
		return NER_VALUE
	else:
		return NA_VALUE

#get NP head noun
def getHeadFeatures(chunk):
	head = None
	word = str(chunk.words[-1].type)
	if word.startswith('NN'):
		head = chunk.words[-1]
	else:
		head = chunk.head
	return head

#get article and its string
def getArticle(chunk):
	article = filter(lambda word:word.type == 'DT', chunk.words)
	if len(article) != 1:
		return None, 'NULL'
	#if contains article	
	article = article[0]
	if article.string.lower() == 'the':
		s_article = 'THE'
	elif article.string.lower() == 'a' or article.string.lower() == 'an':
		s_article = 'A'
	else:
		s_article = 'O'
	return article, s_article

#precheck some errors
def precheckArticle(article, sent, head, chunk):
	if article == None:
		return None
	an = article.string.lower()
	if an != 'an' and an != 'a':
		return None
	if head.type.startswith('NNP') or chunk.string.lower().find('few') != -1 or chunk.string.lower().find('many') != -1:
		return None
	index = article.index
	if index > len(sent) - 2: #make sure DT is not the last token in this sentence
		return None

	first_letter = ""
	bef = sent[index + 1]['w'].lower()	
	if PRON.has_key(bef):
		bef_pron = PRON[bef]
		first_letter = bef_pron[0][0][0]
	else: return None

	start = sent[index]['b']
	end = sent[head.index]['e']

	er = None
	if first_letter not in AEIOU and an == 'an':
		if head.type.startswith('NNS'):
			output = ' '.join([w['w'] for w in sent[(index + 1):(head.index + 1)]])
			er = Error(start, end, output, 'remove \"an\" or change \"an\" to \"the\"', 'ARTICLE_AN_FOR_PLURAL')
		else:
			output = 'a ' + ' '.join([w['w'] for w in sent[(index + 1):(head.index + 1)]])
			er = Error(start, end, output, 'chang \"an\" to \"a\"', 'ARTICLE_AN_ERROR')
	elif first_letter in AEIOU and an == 'a':
		if head.type.startswith('NNS'):
			output = ' '.join([w['w'] for w in sent[(index + 1):(head.index + 1)]])
			er = Error(start, end, output, 'remove \"a\" or change \"a\" to \"the\"', 'ARTICLE_A_FOR_PLURAL')
		else:
			output = 'an' + ' '.join([w['w'] for w in sent[(index + 1):(head.index + 1)]])
			er = Error(start, end, output, 'chang \"a\" to \"an\"', 'ARTICLE_A_ERROR')
	elif head.type.startswith('NNS'):
		output = ' '.join([w['w'] for w in sent[(index):(head.index)]]) + ' ' + head.lemma
		if an == 'an':
			er = Error(start, end, output, 'chang plural to singular or remove \"an\"', 'ARTICLE_AN_FOR_PLURAL')
		else:
			er = Error(start, end, output, 'chang plural to singular or remove \"a\"', 'ARTICLE_A_FOR_PLURAL')
	else: er = None

	#if not None, set original sentence and new sentence for language model check
	if er != None:
		er.set_original(" ".join([w['w'] for w in sent]))
		er.set_newSent(getNewSent(sent,er.output, chunk))
		return er

#get new sentence after precheck article
def getNewSent(sent, output, chunk):
	c_start = chunk.start
	c_end = chunk.stop
	s = map(lambda w:w['w'], sent)
	s[c_start] = output.strip()
	for i in s[(c_start+1):c_end]:
		s.remove(i)
	return " ".join([w for w in s])

#get 3 pos before and after NP head
def getAround(index, sentence, article):
	b = ['NA', 'NA', 'NA']
	a = ['NA', 'NA', 'NA']
	words = sentence.words
	for i in range(3):
		if index + 1 + i > len(words) - 1:
			a[i] = 'NA'
		else:
			a[i] = words[index + 1 + i].type

	if article == None:
		for i in range(3):
			if index - i - 1 < 0:
				b[i] = 'NA'
			else:
				b[i] = words[index - i - 1].type
	else:
		words = filter(lambda item:item.index != article.index, words)
		for i in range(3):
			if index - 1 - i - 1 < 0:
				b[i] = 'NA'
			else:
				b[i] = words[index - 1 - i - 1].type
	return b, a

#get word and pos before NP
def getBeforeNP(chunk, sent):
	s_index = chunk.start
	if s_index -1 < 0:
		return 'NA', 'NA'
	else:
		return sent.words[s_index - 1].string, sent.words[s_index - 1].type 

#get word and pos after NP
def getAfterNP(chunk, sent):
	e_index = chunk.stop
	if e_index > sent.stop - 1:
		return 'NA', 'NA'
	else:
		return sent.words[e_index].string, sent.words[e_index].type

#get wordnet of NP head noun
def getWordNet(head):
	s = wordnet.synsets(head.string.lower())
	if len(s) > 0:
		a = s[0].lexname
		if a == None:
			return 'O'
		return a.replace("noun.", "")
	return 'O'

#get preposition modify
def prepModify(chunk):
	next_chunk = chunk.next(type=None)
	if next_chunk == None:
		return 'NA', 'NA'
	else:
		if next_chunk.type == 'PP':
			word = next_chunk.words[-1]
			return word.type, word.string
		else:
			return 'NA', 'NA'

def getChunkFeatures(chunk):
	relation = chunk.role
	if relation == None:
		relation = "NA"
	pdt = "N"
	prp = "N"
	adj = "NA"
	adj_grade = "NA"
	for w in chunk.words:
		if w.type == 'JJ':
			adj = w.lemma
			adj_grade = 'N'
		elif w.type == 'JJR':
			adj = w.lemma
			adj_grade = 'C'
		elif w.type == 'JJS':
			adj = w.lemma
			adj_grade = 'S'
		elif w.type == 'PDT':
			pdt = "Y"
		elif w.type == 'PRP$':
			prp = "Y"
		else: pass
	return adj, adj_grade, pdt, prp, relation

def getCount(noun):
	if noun.type.startswith('NNS') or noun.type.startswith('NNPS'):
		return 'P'
	else: return 'S'

def getRef(lists, head, sHeads):
	flag = "N"
	w = head.string.lower()
	if w in sHeads:
		flag = "Y"
	for l in lists:
		if w in sHeads:
			flag = "Y"
	return flag

def isVowel(chunk, article):
	word = None
	if article == None:
		word = chunk.words[0]
	else:
		if article.index + 1 - chunk.start > 0 and article.index + 1 - chunk.start < len(chunk.words):
			word = chunk.words[article.index + 1 - chunk.start]
		else:
			word = chunk.words[1]
	first_letter = ""
	if PRON.has_key(word.string.lower()):
		bef_pron = PRON[word.string.lower()]
		first_letter = bef_pron[0][0][0]
	else:
		return 0
	if first_letter in AEIOU:
		return 1
	else:
		return 0