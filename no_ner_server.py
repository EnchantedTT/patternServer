from pattern.en import parse, parsetree, wordnet, NOUN
import sys
import json
from flask import Flask, request, jsonify
from flask_json import FlaskJSON, JsonError, json_response, as_json
from nltk.corpus import cmudict
from BasicModels import ArticleError

app = Flask(__name__)
FlaskJSON(app)

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

NOUNLIST = "NounMap.list"
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

def getHeadFeatures(chunk):
    head = None
    word = str(chunk.words[-1].type)
    if word.startswith('NN'):
        head = chunk.words[-1]
    else:
        head = chunk.head
    if head == None:
        return None, None
    pos = str(head.type)
    isPlural = 'S'
    if pos.startswith('NNPS') or pos.startswith('NNS'):
        isPlural = 'P'
    return head, isPlural

def getRef(lists, head):
    flag = "N"
    for l in lists:
        for h in l:
            if h == head.string.lower():
                flag = "Y"
    return flag

def getWordNet(head):
    s = wordnet.synsets(head.string.lower())
    if len(s) > 0:
        a = s[0].lexname
        if a == None:
            return "O"
        return a.replace("noun.", "")
    else:
        return "O"

def prepModify(chunk):
    next_chunk = chunk.next(type=None)
    if next_chunk == None:
        return "NA", "NA"
    else:
        if next_chunk.type == "PP":
            word = next_chunk.words[-1]
            return word.type, word.string
        else:
                return "NA", "NA"

def getBeforeNP(chunk, sent):
    s_index = chunk.start
    if s_index -1 < 0:
        return "NA", "NA"
    else:
        return sent.words[s_index - 1].string, sent.words[s_index - 1].type 
    
def getAfterNP(chunk, sent):
    e_index = chunk.stop
    if e_index > sent.stop - 1:
        return "NA", "NA"
    else:
        return sent.words[e_index].string, sent.words[e_index].type 

def isDT(word):
    if word.type == "DT":
        return True
    else:
        return False

def getArticle(chunk):
    article = filter(isDT, [word for word in chunk.words])
    if len(article) != 1:
        return None, 'NULL'
    else:
        article = article[0]
        if article.string.lower() == 'the':
            s_article = 'THE'
        elif article.string.lower() == 'a' or article.string.lower() == 'an':
            s_article = 'A'
        else:
            s_article = 'O'
        return article, s_article

PRON = cmudict.dict()
AEIOU = ['A', 'E', 'I', 'O', 'U']
def precheck(article, sent, head, chunk):
    if article == None:
        return None
    if head.type.startswith('NNP') or chunk.string.find('few') != -1 or chunk.string.find('many') != -1:
        return None
    an = article.string.lower()
    if an != 'an' and an != 'a':
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
    end = sent[index + 1]['e']
    if first_letter not in AEIOU and an == 'an':
        if head.type.startswith('NNS') or head.type.startswith('NNPS'):
            b_words = ' '.join([w['w'] for w in sent[(index + 1):(head.index + 1)]])
            output = b_words + "/" + "the " + b_words
            return ArticleError(start, end, output, 'remove \"an\" or change \"an\" to \"the\"')
        else:
            return ArticleError(start, end, ' '.join(['a', bef]), 'chang \"an\" to \"a\"')
    elif first_letter in AEIOU and an == 'a':
        if head.type.startswith('NNS') or head.type.startswith('NNPS'):
            b_words = ' '.join([w['w'] for w in sent[(index + 1):(head.index + 1)]])
            output = b_words + "/" + "the " + b_words
            return ArticleError(start, end, output, 'remove \"a\" or change \"a\" to \"the\"')
        else:
            return ArticleError(start, end, ' '.join(['an', bef]), 'chang \"a\" to \"an\"')
    elif head.type.startswith('NNS') or head.type.startswith('NNPS'):
        end = sent[head.index]['e']
        output = ' '.join([w['w'] for w in sent[(index):(head.index)]]) + ' ' + head.lemma + "/" + ' '.join([w['w'] for w in sent[(index + 1):(head.index + 1)]])
        return ArticleError(start, end, output, 'chang plural to singular or remove \"' + article.string + '\"')
    else: return None

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

def classifyArticle(data):
    data = json.dumps(data, indent=4)
    sentences = json.loads(data)
    errors = []
    features = []
    headList = []
    count = -1
    for sent in sentences:
        count += 1
        text = ' '.join(w['w'] for w in sent)
        s = parsetree(text, relations=True, lemmata=True)
        if len(s) != 1:
            continue #ignore sentence which parse into two
        s = s[0]
        if s.stop != len(sent):
            continue #parse into different len of sentence

        sHeads = []
        for chunk in s.chunks:
            #get NP chunk
            if chunk.type == 'NP':
                #get NP head           
                head, isPlural = getHeadFeatures(chunk)
                if chunk.head.type == 'PRP' or head == None:
                    continue #ignore PRP and None
                #get NP article
                article, s_article = getArticle(chunk)
                if s_article == 'O':  
                    continue #ignore DT which is not a, an or the

                #precheck a/an singular and plural of this NP
                error = precheck(article, sent, head, chunk)
                if error != None:
                    e = dict()
                    e['start'] = error.start
                    e['end'] = error.end
                    e['output'] = error.output
                    e['desc'] = error.description
                    errors.append(e)
                    continue

                #for the rest of the NP chunk, extract features for classifier
                bef3pos, aft3pos = getAround(head.index, s, article)
                bnp_word, bnp_pos = getBeforeNP(chunk, s)
                anp_word, anp_pos = getAfterNP(chunk, s)
                c_list = getCountable(head)
                wordnet = getWordNet(head)
                adj, adj_grade, pdt, prp, relation = getChunkFeatures(chunk)
                pp, pps = prepModify(chunk)
                ref = getRef(headList, head)
                vowel = isVowel(chunk, article)

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
                index.append(count)
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

                sHeads.append(head.string.lower())
        headList.append(sHeads)
        if len(headList) > 5:
            del headList[0]
    return errors, features

@app.route("/article", methods=['POST'])
def hello():
    # We use 'force' to skip mimetype checking to have shorter curl command.
    data = request.get_json(force=True)
    result = dict()
    try:
        value = data['text']
        errors, features = classifyArticle(value)
        result['errors'] = errors
        result['features'] = features
    except (KeyError, TypeError, ValueError):
        raise JsonError(description='Invalid value.')
    return jsonify(result)
    #data = request.form['text']
    #return jsonify(getAllFeatures(data))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5011)